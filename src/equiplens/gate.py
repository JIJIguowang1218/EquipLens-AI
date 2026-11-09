"""R1.5 CLIP 零样本门卫（多模态 L1 层：本地 CPU、零 API 成本、每图约 22ms）。

借鉴自调研（docs/retrieval-tooling-research.md §11）：nsfw-filter 的本机零样本
过滤模式 + LAION 生态"爬取→CLIP 过滤→入库"管线。

判定: 图片嵌入与"保留标签集"和"无关标签集"竞争, 裕量(keep-best − drop-best)
过阈值放行; 阈值经历史人工判定校准(30 样本 93% 一致)。
场景分类(独立于拦截): 放行图再判 single/multi/part 场景; v4 起
`multi_vehicle` 不再硬拒(经销商场地/新闻图常是“主体一台 + 背景一排车”),
只记 `background_vehicles` 提示并限制在参考层——概览/部件名额仍要求单主体。
标签集 v2(2026-10-15 第三轮审核反馈): 增"客车""多车排列"反例标签。
标签集 v3(2026-11-09 W1 冒烟复盘): 增"内饰舱""网格拼图""网页截图""广告字"
四个反例。回归口径: 53 张 360 实图, 同一批字节上 v2 标签集通过 34 → v3 通过 31,
被拒 3 张(2 张拼图 + 1 张内饰), 其余 31 张零误杀(其中 1 张仅 ±0.001 边界)。
标签集 v4(2026-11-09 二次复盘): keep 集增第 4 条“主体一台、背景另有停车”,
multi_vehicle 从硬拒降为提示(只进参考层)。实测 13 张“背景多车”误杀 13/13 恢复,
9 张真坏图仍拒。
证据见 docs/image-filter-pipeline.md §7 与
data-test/runs/web-reassess-20261109/report.md。

**视角不是可靠信号**: 同一批图上 classify_view 的 top1−top2 差值中位数仅
~0.003(6 个标签几乎同分), 所以视角只作提示(`assess_image` 的 exterior_hint),
不得当硬门槛; 旧 `check_exterior` 把视角当硬门槛, 会把正视角整车误杀。

**两段式门卫**（2026-11-09 追加）:
  第一段 `prefilter()` 纯确定性、零模型（字节数/可解码/格式/动图/宽高/长宽比/
  近空白），只挡“CLIP 救不回来”的图（破图、banner、白底占位、缩略图级过小）；
  尺寸下限是 320（不是概览层的 800，否则会丢 640px 的真车图）；
  第二段才是 CLIP `check()`（keep/drop 标签竞争）+ 场景 + 视角。
  分层判定 `assess_from_gate` 吃两段的结果，`gate_skipped=True` 表示
  这张图没进 CLIP——这是两段式省下来的推理。
"""

from __future__ import annotations

import io
import os
import time

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")  # 国内模型下载镜像
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

MODEL_NAME = "unum-cloud/uform3-image-text-english-small"

LEGACY_KEEP_LABELS = [
    "a photo of a single heavy truck, the whole vehicle clearly visible",
    "a photo of a single construction machinery vehicle, like a crane or loader, fully visible",
    "a close-up photo of a truck part, like a bumper, grille, ladder or side guard",
]
KEEP_LABELS = LEGACY_KEEP_LABELS + [
    # v4（2026-11-09）：经销商场地/新闻图常见“主体一台 + 背景一排车”。
    # 实测 13 张被旧 keep 集判成“多车队列”的图，加这条后 13/13 恢复，
    # 而 9 张真坏图（拼图/内饰/文档/图表/客车）仍然被拒。见 image-filter-pipeline §9。
    "a photo of one truck in the foreground with other trucks parked in the background",
]
# v2 基础反例（2026-10-15 第三轮审核反馈）。保留为独立常量，方便 A/B 重算
# “旧标签集 vs v3”时严格同字节对照（见 scripts/reassess_smoke.py）。
BASE_DROP_LABELS = [
    "a photo of a passenger bus or coach",
    "a photo of a row or lineup of many parked trucks",
    "an image of a logo, icon or QR code",
    "a chart, diagram or map",
    "a photo of people, a meeting or an event",
    "a photo of a building, office or factory interior",
    "a text document or article screenshot",
]
# v3（2026-11-09）：W1 冒烟暴露的漏网图（内饰舱 / 网格拼图 / 网页截图 / 广告字）
V3_DROP_LABELS = [
    "a photo of the interior cabin of a truck, seats and dashboard",
    "a grid or collage made of several different truck photos",
    "a screenshot of a web page with text and buttons",
    "an advertisement image with large text overlay and a price",
]
DROP_LABELS = BASE_DROP_LABELS + V3_DROP_LABELS
GATE_LABEL_VERSION = "v4"  # v4 = v3 的 11 条反例 + keep 集第 4 条（背景多车、主体清晰）
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
        "text_emb": text_emb,
        "scene": {name: text_emb(t) for name, t in SCENE_LABELS.items()},
    }
    return _gate_cache


_label_cache: dict[tuple, dict] = {}
_label_emb_cache: dict[str, object] = {}  # 单条标签文本 → 单位向量


def _emb_for(text: str):
    """按标签文本缓存文本嵌入（v2/v3 标签集共用，A/B 重算不必重编码）。"""
    v = _label_emb_cache.get(text)
    if v is None:
        v = _get_gate()["text_emb"](text)
        _label_emb_cache[text] = v
    return v


def classify_labels(data: bytes, labels: dict[str, str]) -> dict:
    """任意标签的零样本打分（复用缓存模型；文本嵌入按标签集缓存）。"""
    g = _get_gate()
    np, Image = g["np"], g["Image"]
    key = tuple(sorted(labels.items()))
    embs = _label_cache.get(key)
    if embs is None:
        embs = {k: g["text_emb"](t) for k, t in labels.items()}
        _label_cache[key] = embs
    try:
        img = g["ip"](Image.open(io.BytesIO(data)))
        emb = np.asarray(g["ie"].encode(img, return_features=False)).ravel()
        emb = emb / (np.linalg.norm(emb) + 1e-9)
    except Exception:  # noqa: BLE001
        return {}
    return {k: round(float(emb @ v), 4) for k, v in embs.items()}


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
    ranked = sorted(scores.values(), reverse=True)
    # top1−top2：实测中位数仅 ~0.003，说明这个分数几乎不可分；
    # 调用方应据此判断“视角可信/不可信”，而不是把 view 当硬事实。
    gap = round(ranked[0] - ranked[1], 4)
    return {"view": best, "score": round(scores[best], 4), "gap": gap,
            "scores": {k: round(v, 4) for k, v in scores.items()}}


EXTERIOR_VIEWS = ("hero_45", "side", "front", "rear")
VIEW_GAP_TRUSTED = 0.01  # top1−top2 低于此值：视角基本不可信

# ---- 第一段：确定性预筛（零模型） -------------------------------------------
# 只挡“CLIP 救不回来”的图。任何一条都必须是硬事实（尺寸/字节/像素统计），
# 判不准的（内饰、多车、广告字）留给第二段 CLIP。
PREFILTER_MIN_WIDTH = 350        # 与 imagesearch.MIN_IMG_WIDTH 一致（历史底线）
PREFILTER_MIN_LONG_SIDE = 320    # 只挡缩略图级垃圾；800/1200 的可用性交给分层
PREFILTER_MAX_BYTES = 8 * 1024 * 1024
PREFILTER_MAX_ASPECT = 4.0       # 长宽比 >4：banner / 长条截屏
PREFILTER_MIN_STD = 6.0          # 64×64 灰度标准差 <6：近空白/纯色占位


def prefilter(data: bytes) -> dict:
    """第一段门卫：纯确定性预筛（零模型，约 1–3ms）。

    返回 dict：
      ok        是否进入第二段 CLIP
      reasons[] 否决理由（empty/too_large/undecodable/animated/too_small/
                extreme_aspect/near_uniform）
      width/height/long_side/aspect/pixels/bytes/format/animated/std/ms

    设计原则：**宁可漏放，不可错杀**。这里判不出语义，所以只做尺寸、字节、
    格式、像素统计四类硬事实；拼图/内饰/广告留给 CLIP。

    尺寸门槛的口径（2026-11-09 调整两次）：**预筛不承担可用性判断**。
    实测 30 张 600px 左右的图被最初的 800 拦下，其中 18 张 CLIP 门卫会放行
    （17 张还是部件特写）——在爬取受限的环境下等于白丢素材。现在第一段只挡
    `long_side < 320` / `width < 350` 的缩略图级垃圾；800/1200 由
    `assess_from_gate` 分层判（概览/部件/参考）。
    """
    from PIL import Image

    t0 = time.perf_counter()
    raw = data or b""
    out = {
        "ok": True, "stage": "prefilter", "reasons": [], "bytes": len(raw),
        "format": "", "width": 0, "height": 0, "long_side": 0, "short_side": 0,
        "aspect": 0.0, "pixels": 0, "animated": False, "std": None,
        "ms": 0.0,
    }
    reasons: list[str] = out["reasons"]
    if not raw:
        reasons.append("empty")
    elif len(raw) > PREFILTER_MAX_BYTES:
        reasons.append("too_large")

    if raw:
        try:
            with Image.open(io.BytesIO(raw)) as im:
                out["format"] = (im.format or "").lower()
                try:
                    out["animated"] = int(getattr(im, "n_frames", 1)) > 1
                except Exception:  # noqa: BLE001
                    out["animated"] = False
                if out["animated"]:
                    reasons.append("animated")
                w, h = im.size
                out["width"], out["height"] = int(w), int(h)
                long_side, short_side = max(int(w), int(h)), min(int(w), int(h))
                out["long_side"], out["short_side"] = long_side, short_side
                out["aspect"] = round(long_side / max(short_side, 1), 3)
                out["pixels"] = int(w) * int(h)
                if int(w) < PREFILTER_MIN_WIDTH or long_side < PREFILTER_MIN_LONG_SIDE:
                    reasons.append("too_small")
                if out["aspect"] > PREFILTER_MAX_ASPECT:
                    reasons.append("extreme_aspect")
                # 近空白/纯色：白底网页截图、占位图、纯色 banner
                try:
                    small = im.convert("L").resize((64, 64))
                    vals = list(small.getdata())
                    mean = sum(vals) / len(vals)
                    var = sum((v - mean) ** 2 for v in vals) / len(vals)
                    out["std"] = round(var ** 0.5, 1)
                    if out["std"] < PREFILTER_MIN_STD:
                        reasons.append("near_uniform")
                except Exception:  # noqa: BLE001
                    pass
        except Exception as e:  # noqa: BLE001
            reasons.append("undecodable")
            out["error"] = f"{type(e).__name__}: {e}"

    out["ok"] = not reasons
    out["ms"] = round((time.perf_counter() - t0) * 1000, 1)
    return out


def check_exterior(data: bytes, threshold: float = DEFAULT_THRESHOLD,
                   allowed_views: tuple[str, ...] = EXTERIOR_VIEWS) -> dict:
    """整车外观判定 = 门卫放行 + 视角属于外观。

    **保守口径**：把 CLIP 视角当硬门槛，会误杀“被猜成 detail/interior”的正视角
    整车（实测 53 张里视角差值中位数 0.003）。检索中 ACTIVE VERIFY 请用
    `assess_image`（视角只作 hint）；这里保留给“宁可少收、不能收错”的主图快筛。

    门卫本身**故意保留部件特写**（KEEP_LABELS 第三条，供部件页裁图用），
    所以选“整车主图”时还要再加一道视角判定，否则内饰/局部结构图会混进来。
    v3 起门卫已补内饰/拼图反例，因此这道视角门槛主要是隐私兜底。
    """
    g = check(data, threshold)
    if not g.get("pass"):
        return dict(g, exterior=False, reason="gate_drop")
    v = classify_view(data)
    ok = v.get("view") in allowed_views
    return dict(g, view=v.get("view"), view_score=v.get("score"),
                view_gap=v.get("gap"),
                view_trusted=(v.get("gap") or 0) >= VIEW_GAP_TRUSTED,
                exterior=ok,
                reason="ok" if ok else f"not_exterior:{v.get('view')}")


def assess_image(data: bytes, *, min_overview: int = 800,
                 min_part: int = 1200) -> dict:
    """两段式评估一张图（预筛 → CLIP → 分层），替代单一布尔值。

    第一段 `prefilter` 不通过时**不进 CLIP**，直接返回 `stage="prefilter"`
    与 `gate_skipped=True`（省一次模型推理，理由仍是可解释的硬事实）；
    通过则走第二段 `check` + 视角，再按用途分层：
      overview_candidate = 门卫通过 + 长边 ≥ min_overview + 不是多车拼图
      part_candidate     = 门卫通过 + 长边 ≥ min_part     + 不是多车拼图
    视角**不参与否决**，只给 `exterior_hint`（视角属外观）与 `view_trusted`
    （top1−top2 是否够大）。理由：
      - 视角零样本 top1−top2 中位数 ~0.003，当硬门槛会误杀正视角整车；
      - 门卫 v3 已补内饰/拼图/网页截图/广告反例，坏图主要靠它挡。
    例外：view=interior 且 gap ≥ VIEW_GAP_TRUSTED 视为强信号，直接判不可用
    （避免“门卫漏放的内饰图”被当成外观候选）。
    """
    p = prefilter(data)
    if not p["ok"]:
        return _assess_blocked(p, min_overview, min_part)
    g = check(data)
    width, height = p["width"], p["height"]
    v = classify_view(data) if g.get("pass") else {}
    return assess_from_gate(g, v, width, height, min_overview=min_overview,
                            min_part=min_part, prefilter_result=p)


def _assess_blocked(p: dict, min_overview: int, min_part: int) -> dict:
    """第一段就否决：返回与 assess_from_gate 同构的结果（CLIP 未运行）。"""
    long_side = int(p.get("long_side") or 0)
    return {
        "pass": False, "keep": None, "drop": None, "margin": None,
        "keep_label": "", "drop_label": "",
        "scene": None, "width": int(p.get("width") or 0),
        "height": int(p.get("height") or 0), "long_side": long_side,
        "view": "", "view_score": -1.0, "view_gap": 0.0, "view_trusted": False,
        "exterior_hint": False,
        "overview_candidate": False, "part_candidate": False,
        "reference_candidate": False,
        "interior_suspect": False, "multi_vehicle": False,
        "stage": "prefilter", "gate_skipped": True, "prefilter": p,
        "reasons": list(p.get("reasons") or []),
        "hints": [],
    }


def assess_from_gate(gate_result: dict, view_result: dict, width: int,
                     height: int, *, min_overview: int = 800,
                     min_part: int = 1200, prefilter_result: dict | None = None) -> dict:
    """用已算好的两段结果拼装分层判定（冒烟/引擎复用，避免重复编码）。

    `prefilter_result` 由调用方传入可省一次解码与像素统计；不传则视为已过
    第一段（兼容旧调用）。
    """
    p = prefilter_result or {}
    if p and not p.get("ok", True):
        return _assess_blocked(p, min_overview, min_part)
    g = gate_result or {}
    v = view_result or {}
    passed = bool(g.get("pass"))
    scene = g.get("scene")
    long_side = max(int(width or 0), int(height or 0))
    reasons: list[str] = []   # 否决理由（进不可用判定）
    hints: list[str] = []     # 提示（视角类，只供人工/排序，不否决）
    view = v.get("view", "") if passed else ""
    gap = float(v.get("gap") or 0.0) if passed else 0.0
    view_score = float(v.get("score") or 0.0) if passed else -1.0

    if not passed:
        reasons.append("gate_drop")
    multi = scene == "multi_vehicle"
    interior_suspect = view == "interior" and gap >= VIEW_GAP_TRUSTED
    if interior_suspect:
        reasons.append("interior_suspect")
    if passed and long_side < min_overview:
        reasons.append("low_res_overview")
    elif passed and long_side < min_part:
        reasons.append("low_res_part")
    if multi:
        # v4：场景里有别的车只作提示，不再一刀切否决（主体可能仍然清晰）；
        # 但它不进“概览/部件”名额，只进参考层，除非后续有主体检测再放开。
        hints.append("background_vehicles")
    if view == "detail":
        hints.append("view_detail_hint")
    elif view and not _view_trusted(gap):
        hints.append("view_uncertain")

    usable_base = passed and not interior_suspect and not multi
    out = {
        "pass": passed,
        "keep": g.get("keep"), "drop": g.get("drop"), "margin": g.get("margin"),
        "keep_label": g.get("keep_label", ""), "drop_label": g.get("drop_label", ""),
        "scene": scene, "width": int(width or 0), "height": int(height or 0),
        "long_side": long_side,
        "view": view, "view_score": round(view_score, 4),
        "view_gap": gap, "view_trusted": _view_trusted(gap),
        # 弱提示：视角标签落在外观四类即记 hint，不要求 gap；gap 另看 view_trusted。
        "exterior_hint": view in EXTERIOR_VIEWS,
        "overview_candidate": usable_base and long_side >= min_overview,
        "part_candidate": usable_base and long_side >= min_part,
        # 低清但语义可用，或“主体 + 背景多车”：可看/可参考，不占“可用”名额
        "reference_candidate": (passed and not interior_suspect
                                and (multi or long_side < min_overview)),
        "multi_vehicle": multi,
        "interior_suspect": interior_suspect,
        "stage": "gate", "gate_skipped": False,
        "prefilter": p or None,
        "reasons": reasons,
        "hints": hints,
    }
    return out



def _view_trusted(gap: float) -> bool:
    return float(gap or 0.0) >= VIEW_GAP_TRUSTED


def _image_size(data: bytes) -> tuple[int, int]:
    from PIL import Image
    try:
        with Image.open(io.BytesIO(data)) as im:
            return im.size
    except Exception:  # noqa: BLE001
        return 0, 0


def check(data: bytes, threshold: float = DEFAULT_THRESHOLD, *,
          drop_labels: list[str] | None = None,
          keep_labels: list[str] | None = None) -> dict:
    """第二段门卫（CLIP）。返回 keep/drop 相似度、裕量、场景、耗时与是否放行。

    `drop_labels` 可换成旧标签集，用于“同一批字节上 v2 vs v3”的严格对照
    （`check_v2` 即 v2 基础反例集），A/B 数字因此是可比的。
    """
    g = _get_gate()
    np, Image = g["np"], g["Image"]
    drops = list(drop_labels if drop_labels is not None else DROP_LABELS)
    keeps = list(keep_labels if keep_labels is not None else KEEP_LABELS)
    t0 = time.perf_counter()
    try:
        img_arr = g["ip"](Image.open(io.BytesIO(data)))
        emb = np.asarray(g["ie"].encode(img_arr, return_features=False)).ravel()
        emb = emb / (np.linalg.norm(emb) + 1e-9)
    except Exception as e:  # noqa: BLE001  # 解码失败交给上游跳过逻辑
        return {"pass": False, "keep": -1.0, "drop": -1.0, "margin": -1.0,
                "scene": None, "ms": 0.0, "error": str(e)}
    keep_scores = [float(emb @ _emb_for(t)) for t in keeps]
    drop_scores = [float(emb @ _emb_for(t)) for t in drops]
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
        "keep_label": keeps[keep_scores.index(keep_best)],
        "drop_label": drops[drop_scores.index(drop_best)],
        "scene": scene,
        "label_count": {"keep": len(keeps), "drop": len(drops)},
        "ms": round((time.perf_counter() - t0) * 1000, 1),
    }


def check_v2(data: bytes, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """用 v2 基础反例集重算（同字节对照 v3 用；不进生产链路）。"""
    return check(data, threshold, drop_labels=BASE_DROP_LABELS,
                 keep_labels=LEGACY_KEEP_LABELS)

