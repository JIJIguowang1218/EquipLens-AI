"""判向探针 v2：Chinese-CLIP 大底座特征 + 人工标注最近质心（意见 #9/#11 攻坚线）。

v1（UForm3-small 特征）留一准确率仅 36%——零样本 1%→36% 证明"标注训探针"路线
成立, 瓶颈在小模型特征弱。v2 换 Chinese-CLIP ViT-B/16（中文跨模态大底座）提特征,
质心法与评测口径不变, 数据（人工标注）与尺子（留一准确率）直接复用。

方向口径 = 规范 v0.2.3：前=车头方向, 左右=驾驶员视角。
训练类 = 人工标注的方向类: hero_lf / hero_rf / side_l / front
（rear 与 side_r 暂无人工样本, 不进训练集; side_r 用镜像法推断, 见下）。

镜像法（side_r 数据缺口的无样本解）：CLIP 特征对水平镜像敏感, 正侧图翻转后
与 side_l 质心的相似度会反转——原图更像左侧像判 side_l, 翻转图更像判 side_r。
用 9 张 side_l 人工样本做镜像一致性检验（原图相似度应高于翻转图）。

标注来源口径: confirm_log 中 field=view_angle 的 latest 记录, method='single'
（review-serve 人工点击）为训练集; method='batch'（op-view 机器零样本重打标 /
op-probe 探针自动定向）为机器值, 是 v2 的复查对象。
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")  # 国内模型下载镜像
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

CLIP_MODEL = "OFA-Sys/chinese-clip-vit-base-patch16"
CLIP_MODEL_L = "OFA-Sys/chinese-clip-vit-large-patch14"  # 大底座（B/16 特征弱时升级档）
DIRECTION_CLASSES = ["hero_lf", "hero_rf", "side_l", "front", "rear"]
MIRROR_PAIR = {"side_l": "side_r", "side_r": "side_l"}
# 镜像对称视角: 水平翻转的左前45°图就是右前45°图（物理成立）——
# 翻转增广让 hero_rf 从 21 条变 67 条、side_r 无中生有, 且左右信号加倍
MIRROR_VIEW = {"hero_lf": "hero_rf", "hero_rf": "hero_lf",
               "side_l": "side_r", "side_r": "side_l",
               "front": "front", "rear": "rear"}

_factories = {"chinese-clip": lambda: _make_chinese_clip(CLIP_MODEL),
              "chinese-clip-l": lambda: _make_chinese_clip(CLIP_MODEL_L),
              "uform": lambda: _make_uform()}
_backends: dict = {}


def get_backend(name: str):
    """惰性加载特征后端, 返回 encode(paths) -> 归一化特征矩阵 [N, D]。进程内单例。"""
    if name not in _factories:
        raise ValueError(f"未知后端 {name!r}（可选: chinese-clip / chinese-clip-l / uform）")
    if name not in _backends:
        _backends[name] = _factories[name]()
    return _backends[name]


def _make_chinese_clip(model_name: str = CLIP_MODEL):
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor, ChineseCLIPModel

    model = ChineseCLIPModel.from_pretrained(model_name)
    model.eval()
    proc = AutoProcessor.from_pretrained(model_name)

    def encode(paths: list[Path]) -> "np.ndarray":
        feats = []
        with torch.no_grad():
            for i in range(0, len(paths), 8):
                imgs = [Image.open(p).convert("RGB") for p in paths[i:i + 8]]
                inputs = proc(images=imgs, return_tensors="pt")
                out = model.get_image_features(pixel_values=inputs["pixel_values"])
                # transformers 4.x 返回张量; 5.x 返回输出对象, 投影特征在 pooler_output
                t = out if torch.is_tensor(out) else (
                    out.image_features if getattr(out, "image_features", None) is not None
                    else out.pooler_output)
                t = t / t.norm(dim=-1, keepdim=True)
                feats.append(t.numpy())
        return np.concatenate(feats, axis=0)

    return encode


def _make_uform():
    """UForm 基线后端（v1 同款特征, 用于同口径对比）。仅加载图像编码器。"""
    import numpy as np
    from PIL import Image
    from uform import get_model_onnx
    from uform.shared import Modality

    procs, encs = get_model_onnx(
        "unum-cloud/uform3-image-text-english-small", modalities=(Modality.IMAGE_ENCODER,))
    ip = procs[Modality.IMAGE_ENCODER]
    ie = encs[Modality.IMAGE_ENCODER]

    def encode(paths: list[Path]) -> "np.ndarray":
        arr = np.asarray([np.asarray(ie.encode(ip(Image.open(p).convert("RGB")),
                                               return_features=False)).ravel()
                          for p in paths], dtype=np.float32)
        return arr / (np.linalg.norm(arr, axis=-1, keepdims=True) + 1e-9)

    return encode


# ---------- 特征缓存（npz, 按 sha256+后端 键, 复跑不重提） ----------

def extract_cached(data_dir: Path, backend: str, items: list[dict]) -> dict[str, "np.ndarray"]:
    """items: [{key, path}]（key=sha256[:16] + ':flip' 可选翻转）。
    返回 key -> 特征向量。缓存 data-test/probe-features-<backend>.npz。"""
    import numpy as np
    cache_path = Path(data_dir) / f"probe-features-{backend}.npz"
    cache: dict[str, "np.ndarray"] = {}
    if cache_path.exists():
        z = np.load(cache_path, allow_pickle=False)
        cache = {k: z[k] for k in z.files}
    missing = [it for it in items if it["key"] not in cache]
    if missing:
        encode = get_backend(backend)
        from PIL import Image
        t0 = time.perf_counter()
        # 原图与翻转图分两批提取（批量效率）
        orig = [it for it in missing if not it["key"].endswith(":flip")]
        flipped = [it for it in missing if it["key"].endswith(":flip")]
        if orig:
            F = encode([it["path"] for it in orig])
            for it, v in zip(orig, F):
                cache[it["key"]] = v.astype(np.float32)
        if flipped:
            tmp_dir = Path(data_dir) / "cache" / "probe-flip"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmppaths = []
            for it in flipped:
                src = it["path"]
                out = tmp_dir / (hashlib.sha256(str(src).encode()).hexdigest()[:16] + ".png")
                if not out.exists():
                    Image.open(src).convert("RGB").transpose(Image.FLIP_LEFT_RIGHT).save(out)
                tmppaths.append(out)
            F = encode(tmppaths)
            for it, v in zip(flipped, F):
                cache[it["key"]] = v.astype(np.float32)
        np.savez(cache_path, **cache)
        print(f"  特征提取 {backend}: 新提 {len(missing)} 项, "
              f"耗时 {time.perf_counter() - t0:.1f}s（缓存 {cache_path.name}）")
    return cache


# ---------- 质心探针与留一验证（纯 numpy, 可独立单测） ----------

def fit_centroids(feats, labels: list[str]) -> dict[str, "np.ndarray"]:
    """类质心 = 类内特征均值后归一化。feats: [N, D] 已归一化。"""
    import numpy as np
    out = {}
    for c in sorted(set(labels)):
        v = np.asarray([f for f, l in zip(feats, labels) if l == c]).mean(axis=0)
        out[c] = v / (np.linalg.norm(v) + 1e-9)
    return out


def fit_centroids_mirror(feats, flip_feats, labels: list[str]) -> dict[str, "np.ndarray"]:
    """镜像增广质心: (原图, 标签) + (翻转图, 镜像标签) 一起拟合。
    side_r 无人工样本时由 side_l 翻转图无中生有; hero_rf 21→67 条平衡类别。"""
    return fit_centroids(list(feats) + list(flip_feats),
                         list(labels) + [MIRROR_VIEW[l] for l in labels])


def predict_symmetric(feat, flip_feat, centroids: dict) -> dict:
    """镜像对称判定: S(c) = cos(原图, c) + cos(翻转图, 镜像类(c))。
    物理含义: 假设 x 是左前, 则翻转图应像右前——两侧证据互证,
    左右差异信号加倍（CLIP 左右质心间距小, 单侧证据太弱）。"""
    scores = {}
    for c, v in centroids.items():
        s = float(feat @ v)
        mc = MIRROR_VIEW.get(c, c)
        if flip_feat is not None and mc in centroids:
            s += float(flip_feat @ centroids[mc])
        scores[c] = s / 2.0
    rank = sorted(scores, key=scores.get, reverse=True)
    return {"view": rank[0], "margin": round(scores[rank[0]] - scores[rank[1]], 4),
            "scores": {k: round(v, 4) for k, v in scores.items()}}


def predict_one(feat, centroids: dict) -> dict:
    """最近质心判定。返回类、裕量（best − second）与全部相似度。"""
    scores = {c: float(feat @ v) for c, v in centroids.items()}
    rank = sorted(scores, key=scores.get, reverse=True)
    second = scores[rank[1]] if len(rank) > 1 else scores[rank[0]]
    return {"view": rank[0], "margin": round(scores[rank[0]] - second, 4),
            "scores": {k: round(v, 4) for k, v in scores.items()}}


def predict_direction(feat, flip_feat, centroids: dict) -> dict:
    """方向判定（含镜像法）：side 命中时用 原图/翻转图 对 side_l 质心的相似度分左右。"""
    r = predict_one(feat, centroids)
    if r["view"] == "side_l" and flip_feat is not None:
        s_orig, s_flip = float(feat @ centroids["side_l"]), float(flip_feat @ centroids["side_l"])
        if s_flip > s_orig:
            r["view"] = "side_r"
            r["mirror"] = {"orig": round(s_orig, 4), "flip": round(s_flip, 4)}
    return r


def loo_eval(feats, labels: list[str]) -> dict:
    """留一验证：每条样本用"去掉自身后"的质心判定。返回准确率/各类召回/混淆/错例。"""
    import numpy as np
    feats = np.asarray(feats)
    labels = list(labels)
    n_ok = 0
    confusion: Counter = Counter()
    errors = []
    per_class_total = Counter(labels)
    per_class_ok: Counter = Counter()
    for i in range(len(labels)):
        rest_f = np.delete(feats, i, axis=0)
        rest_l = [l for j, l in enumerate(labels) if j != i]
        cents = fit_centroids(rest_f, rest_l)
        pred = predict_one(feats[i], cents)["view"]
        if pred == labels[i]:
            n_ok += 1
            per_class_ok[labels[i]] += 1
        else:
            confusion[(labels[i], pred)] += 1
            errors.append({"index": i, "true": labels[i], "pred": pred,
                           "margin": predict_one(feats[i], cents)["margin"]})
    return {"n": len(labels), "accuracy": round(n_ok / len(labels), 4),
            "per_class": {c: f"{per_class_ok[c]}/{per_class_total[c]}"
                          for c in sorted(per_class_total)},
            "confusion": [{"true": t, "pred": p, "n": n} for (t, p), n in
                          confusion.most_common()],
            "errors": errors}


def loo_eval_mirror(feats, flip_feats, labels: list[str]) -> dict:
    """留一验证（镜像增广口径）：留 i 时, 原图与翻转图两份样本一并移出。"""
    import numpy as np
    feats, flip_feats = np.asarray(feats), np.asarray(flip_feats)
    labels = list(labels)
    n_ok = 0
    confusion: Counter = Counter()
    errors = []
    per_class_total = Counter(labels)
    per_class_ok: Counter = Counter()
    for i in range(len(labels)):
        keep = [j for j in range(len(labels)) if j != i]
        aug_f = ([feats[j] for j in keep] + [flip_feats[j] for j in keep])
        aug_l = ([labels[j] for j in keep]
                 + [MIRROR_VIEW[l] for l in (labels[j] for j in keep)])
        cents = fit_centroids(aug_f, aug_l)
        r = predict_symmetric(feats[i], flip_feats[i], cents)
        if r["view"] == labels[i]:
            n_ok += 1
            per_class_ok[labels[i]] += 1
        else:
            confusion[(labels[i], r["view"])] += 1
            errors.append({"index": i, "true": labels[i], "pred": r["view"],
                           "margin": r["margin"]})
    return {"n": len(labels), "accuracy": round(n_ok / len(labels), 4),
            "per_class": {c: f"{per_class_ok[c]}/{per_class_total[c]}"
                          for c in sorted(per_class_total)},
            "confusion": [{"true": t, "pred": p, "n": n} for (t, p), n in
                          confusion.most_common()],
            "errors": errors}


def mirror_sanity(feats, flip_feats, labels: list[str], cls: str = "side_l") -> dict:
    """镜像一致性检验：cls 类样本的原图相似度应高于翻转图（否则镜像法不可信）。"""
    import numpy as np
    feats, flip_feats = np.asarray(feats), np.asarray(flip_feats)
    idx = [i for i, l in enumerate(labels) if l == cls]
    if not idx:
        return {"n": 0, "consistent": 0}
    cents = fit_centroids(feats, labels)
    ok = sum(1 for i in idx
             if float(feats[i] @ cents[cls]) > float(flip_feats[i] @ cents[cls]))
    return {"n": len(idx), "consistent": ok}


# ---------- 数据库取数 ----------

def _asset_key(asset_id: str, path: str) -> str:
    """特征缓存键: 资产+路径摘要（:flip 后缀 = 水平翻转图）。"""
    return hashlib.sha256((asset_id + path).encode()).hexdigest()[:16]


def resolve(data_dir, rel: str) -> Path:
    """file_path 相对 data_dir 存储；不存在时回退原样路径（兼容绝对路径）。"""
    p = Path(data_dir) / rel
    return p if p.exists() else Path(rel)


def _latest_view_records(conn, ignore_prefix: str | None = None) -> dict[str, dict]:
    """每素材最新 view_angle 账本记录: {asset_id: {value, method, op_id}}。
    ignore_prefix: 忽略指定前缀的操作（如 op-probe2 自身写入, 保证重跑幂等）。"""
    latest = {}
    sql = """SELECT object_id, confirmed_value, method, op_id FROM confirm_log
             WHERE field='view_angle' AND confirmed_value IS NOT NULL
             ORDER BY object_id, confirmed_at"""
    for oid, val, m, op in conn.execute(sql):
        if ignore_prefix and op.startswith(ignore_prefix):
            continue
        latest[oid] = {"value": json.loads(val), "method": m, "op_id": op}
    return latest


def load_labeled(conn) -> list[dict]:
    """训练集: 最新视角记录来自人工（method=single）的素材及标签（限方向类）。"""
    latest = _latest_view_records(conn)
    out = []
    for oid, rec in latest.items():
        if rec["method"] != "single" or rec["value"] not in DIRECTION_CLASSES:
            continue
        row = conn.execute(
            "SELECT file_path, confirm_status FROM assets WHERE id=?", (oid,)).fetchone()
        if row is None or row["confirm_status"] == "rejected":
            continue
        out.append({"asset_id": oid, "path": row["file_path"], "label": rec["value"]})
    return out


def probe_targets(conn) -> list[dict]:
    """v2 复查对象: 最新视角为机器值, 且 ∈ 过渡态(hero_45/side) 或 op-probe v1 定向。
    忽略 v2 自身（op-probe2）写入, 重跑幂等; 机器 front/rear/detail 等终态值不在
    本轮范围, 随标注积累逐步纳入飞轮。"""
    latest = _latest_view_records(conn, ignore_prefix="op-probe2")
    out = []
    for oid, rec in latest.items():
        if rec["method"] != "batch":
            continue
        transitional = rec["value"] in ("hero_45", "side")
        from_v1 = rec["op_id"].startswith("op-probe")
        if not (transitional or from_v1):
            continue
        row = conn.execute(
            "SELECT file_path, vehicle_id, confirm_status, view_angle FROM assets WHERE id=?",
            (oid,)).fetchone()
        if row is None or row["confirm_status"] == "rejected":
            continue
        out.append({"asset_id": oid, "path": row["file_path"],
                    "vehicle_id": row["vehicle_id"], "current": rec["value"],
                    "reason": "过渡态待定向" if transitional else "v1 探针定向待复查"})
    return out


def fit_from_db(conn, data_dir: Path, backend: str) -> dict:
    """训练集特征（原图+翻转）+ 镜像增广质心（train/eval/suggest 共用）。"""
    import numpy as np
    labeled = load_labeled(conn)
    if not labeled:
        raise ValueError("无人工方向标注（confirm_log method=single 的视角记录）")
    keys = [_asset_key(it["asset_id"], it["path"]) for it in labeled]
    cache = extract_cached(
        data_dir, backend,
        [{"key": k, "path": resolve(data_dir, it["path"])}
         for k, it in zip(keys, labeled)]
        + [{"key": k + ":flip", "path": resolve(data_dir, it["path"])}
           for k, it in zip(keys, labeled)])
    feats = np.asarray([cache[k] for k in keys])
    flips = np.asarray([cache[k + ":flip"] for k in keys])
    labels = [it["label"] for it in labeled]
    return {"labeled": labeled, "feats": feats, "flips": flips, "labels": labels,
            "cents": fit_centroids_mirror(feats, flips, labels)}


def run_eval(conn, data_dir: Path, backend: str) -> dict:
    """留一验证（普通口径 + 镜像增广口径）+ 镜像一致性检验,
    报告落 data-test/probe-eval-<backend>.json。"""
    fit = fit_from_db(conn, data_dir, backend)
    feats, flips, labels = fit["feats"], fit["flips"], fit["labels"]
    rep = {"backend": backend, "classes": dict(sorted(Counter(labels).items())),
           "loo": loo_eval(feats, labels),
           "loo_mirror": loo_eval_mirror(feats, flips, labels)}
    rep["mirror_sanity"] = mirror_sanity(feats, flips, labels)
    rep["summary"] = {"backend": backend, "n": rep["loo"]["n"],
                      "accuracy": rep["loo"]["accuracy"],
                      "accuracy_mirror": rep["loo_mirror"]["accuracy"],
                      "per_class_mirror": rep["loo_mirror"]["per_class"],
                      "mirror_sanity": rep["mirror_sanity"]}
    out = Path(data_dir) / f"probe-eval-{backend}.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    rep["out"] = str(out)
    return rep


def build_suggestions(conn, data_dir: Path, backend: str = "chinese-clip",
                      apply: bool = True) -> dict:
    """对复查对象跑 v2 探针 → 建议 JSON（data-test/probe-suggest.json）+ 落账机器值。
    落账口径: 与现值不同才写（confirm_log 只增不改, op-probe2-* 可整体撤销）;
    side 命中走镜像法分 side_l/side_r。"""
    targets = probe_targets(conn)
    if not targets:
        return {"targets": 0, "applied": 0}
    import numpy as np
    from . import workflow

    fit = fit_from_db(conn, data_dir, backend)
    cents = fit["cents"]
    cache = extract_cached(
        data_dir, backend,
        [{"key": _asset_key(t["asset_id"], t["path"]),
          "path": resolve(data_dir, t["path"])} for t in targets]
        + [{"key": _asset_key(t["asset_id"], t["path"]) + ":flip",
            "path": resolve(data_dir, t["path"])} for t in targets])

    sugg, applied = [], []
    for t in targets:
        k = _asset_key(t["asset_id"], t["path"])
        r = predict_symmetric(cache[k], cache.get(k + ":flip"), cents)
        rec = {"asset_id": t["asset_id"], "vehicle_id": t["vehicle_id"],
               "current": t["current"], "reason": t["reason"],
               "suggested": r["view"], "margin": r["margin"], "scores": r["scores"]}
        if "mirror" in r:
            rec["mirror"] = r["mirror"]
        sugg.append(rec)
        if apply and r["view"] != t["current"]:
            cur_db = conn.execute("SELECT view_angle FROM assets WHERE id=?",
                                  (t["asset_id"],)).fetchone()
            if cur_db is None or cur_db["view_angle"] == r["view"]:
                continue  # 已落过账（重跑幂等）, 不写重复记录
            workflow.set_view(conn, t["asset_id"], r["view"], method="batch",
                              op_id=f"op-probe2-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
            applied.append({"asset_id": t["asset_id"], "from": t["current"], "to": r["view"]})
    out = Path(data_dir) / "probe-suggest.json"
    out.write_text(json.dumps(
        {"backend": backend, "classes": sorted(cents), "generated_at":
         datetime.now().isoformat(timespec="seconds"), "suggestions": sugg},
        ensure_ascii=False, indent=1), encoding="utf-8")
    return {"targets": len(targets), "applied": len(applied), "changed": applied,
            "out": str(out), "suggestions": sugg}
