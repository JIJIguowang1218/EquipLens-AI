"""R1.5 CLIP 零样本门卫（多模态 L1 层：本地 CPU、零 API 成本、每图约 22ms）。

借鉴自调研（docs/retrieval-tooling-research.md §11）：nsfw-filter 的本机零样本
过滤模式 + LAION 生态"爬取→CLIP 过滤→入库"管线。

判定: 图片嵌入与"保留标签集"和"无关标签集"竞争, 裕量(keep-best − drop-best)
过阈值放行; 阈值经历史人工判定校准(30 样本 93% 一致)。
场景分类(独立于拦截): 放行图再判 single/multi/part 场景, 多车排列图放行但
打 multi_vehicle 标记供人工快筛与后续裁切——不做一刀切丢弃。
标签集 v2(2026-10-15 第三轮审核反馈): 增"客车""多车排列"反例标签。
"""

from __future__ import annotations

import io
import os
import time

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")  # 国内模型下载镜像
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

MODEL_NAME = "unum-cloud/uform3-image-text-english-small"

KEEP_LABELS = [
    "a photo of a single heavy truck, the whole vehicle clearly visible",
    "a photo of a single construction machinery vehicle, like a crane or loader, fully visible",
    "a close-up photo of a truck part, like a bumper, grille, ladder or side guard",
]
DROP_LABELS = [
    "a photo of a passenger bus or coach",
    "a photo of a row or lineup of many parked trucks",
    "an image of a logo, icon or QR code",
    "a chart, diagram or map",
    "a photo of people, a meeting or an event",
    "a photo of a building, office or factory interior",
    "a text document or article screenshot",
]
SCENE_LABELS = {
    "single_vehicle": "a photo of a single truck, the whole vehicle clearly visible",
    "multi_vehicle": "a photo of a row or lineup of many parked trucks",
    "part": "a close-up photo of a truck part",
}

DEFAULT_THRESHOLD = 0.0  # 历史人工判定校准(93% 一致)

# 视觉判向标签(v0.2.3): 方向中性——CLIP 分不清左右(约定=驾驶员视角), 不瞎猜,
# 命中 3/4 或正侧时落 hero_45/side 未定态, 人工/VLM 定向升级
VIEW_LABELS = {
    "front": "a photo of a truck viewed from directly in front",
    "rear": "a photo of a truck viewed from directly behind",
    "hero_45": "a photo of a truck from a 3/4 front angle",
    "side": "a photo of a truck from a pure side profile view",
    "interior": "a photo of the interior cabin of a truck",
    "detail": "a close-up photo of a truck part or component",
}

_gate_cache = None


def _get_gate():
    """惰性加载: 模型 + 预编码的标签嵌入（进程内单例）。"""
    global _gate_cache
    if _gate_cache is not None:
        return _gate_cache
    import numpy as np
    from PIL import Image
    from uform import get_model_onnx
    from uform.shared import Modality

    processors, encoders = get_model_onnx(
        MODEL_NAME, modalities=(Modality.TEXT_ENCODER, Modality.IMAGE_ENCODER))
    tp = processors[Modality.TEXT_ENCODER]
    ip = processors[Modality.IMAGE_ENCODER]
    te = encoders[Modality.TEXT_ENCODER]
    ie = encoders[Modality.IMAGE_ENCODER]

    def text_emb(t):
        v = np.asarray(te.encode(tp(t), return_features=False)).ravel()
        return v / (np.linalg.norm(v) + 1e-9)

    _gate_cache = {
        "ip": ip, "ie": ie, "np": np, "Image": Image,
        "keep": [text_emb(t) for t in KEEP_LABELS],
        "drop": [text_emb(t) for t in DROP_LABELS],
        "scene": {name: text_emb(t) for name, t in SCENE_LABELS.items()},
    }
    return _gate_cache


def classify_view(data: bytes) -> dict:
    """视觉判向（CLIP 零样本）: 返回最可能视角与置信，方向不可判时使用未定态。"""
    g = _get_gate()
    np, Image = g["np"], g["Image"]
    try:
        img_arr = g["ip"](Image.open(io.BytesIO(data)))
        emb = np.asarray(g["ie"].encode(img_arr, return_features=False)).ravel()
        emb = emb / (np.linalg.norm(emb) + 1e-9)
    except Exception as e:  # noqa: BLE001
        return {"view": "untagged", "score": -1.0, "error": str(e)}
    # 视角标签嵌入惰性编码
    if "view_embs" not in g:
        import numpy as _np
        from uform import get_model_onnx
        from uform.shared import Modality
        processors, encoders = get_model_onnx(
            MODEL_NAME, modalities=(Modality.TEXT_ENCODER, Modality.IMAGE_ENCODER))
        tp, te = processors[Modality.TEXT_ENCODER], encoders[Modality.TEXT_ENCODER]
        def text_emb(t):
            v = _np.asarray(te.encode(tp(t), return_features=False)).ravel()
            return v / (_np.linalg.norm(v) + 1e-9)
        g["view_embs"] = {name: text_emb(t) for name, t in VIEW_LABELS.items()}
    scores = {name: float(emb @ v) for name, v in g["view_embs"].items()}
    best = max(scores, key=scores.get)
    return {"view": best, "score": round(scores[best], 4),
            "scores": {k: round(v, 4) for k, v in scores.items()}}


def check(data: bytes, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """门卫判定。返回 keep/drop 相似度、裕量、场景、耗时与是否放行。"""
    g = _get_gate()
    np, Image = g["np"], g["Image"]
    t0 = time.perf_counter()
    try:
        img_arr = g["ip"](Image.open(io.BytesIO(data)))
        emb = np.asarray(g["ie"].encode(img_arr, return_features=False)).ravel()
        emb = emb / (np.linalg.norm(emb) + 1e-9)
    except Exception as e:  # noqa: BLE001  # 解码失败交给上游跳过逻辑
        return {"pass": False, "keep": -1.0, "drop": -1.0, "margin": -1.0,
                "scene": None, "ms": 0.0, "error": str(e)}
    keep_scores = [float(emb @ k) for k in g["keep"]]
    drop_scores = [float(emb @ d) for d in g["drop"]]
    keep_best, drop_best = max(keep_scores), max(drop_scores)
    margin = keep_best - drop_best
    scene = None
    if margin >= threshold:
        scene_scores = {name: float(emb @ v) for name, v in g["scene"].items()}
        scene = max(scene_scores, key=scene_scores.get)
    return {
        "pass": margin >= threshold,
        "keep": round(keep_best, 4), "drop": round(drop_best, 4),
        "margin": round(margin, 4),
        "keep_label": KEEP_LABELS[keep_scores.index(keep_best)],
        "drop_label": DROP_LABELS[drop_scores.index(drop_best)],
        "scene": scene,
        "ms": round((time.perf_counter() - t0) * 1000, 1),
    }
