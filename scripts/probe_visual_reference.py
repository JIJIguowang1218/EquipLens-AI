# -*- coding: utf-8 -*-
"""S2-06 可行性探针：image-to-image 每型号参考图库能否区分型号身份。

背景：S2-01（`scripts/probe_visual_identity.py`）证明零样本文本标签（“a photo of
a {model}”）对同一批图没有身份分辨力（3 选 1 top-1 11.0% vs 33.3% 随机）。
本探针换一条路：不靠文本，给每个型号攒一小组参考图，用 UForm3 图像嵌入的
**每型号均值向量（prototype）+ 留一法**做 top-1，看图像本身能否把型号分开。

方法（离线、无 LLM、无新模型下载）：
  1. 复用 `scripts/probe_visual_identity.py` 的语料加载逻辑（同 run glob、按
     asset_id 去重 base 优先、图片必须存在、model 非空），再从
     `state.json.verifications` 补出每个资产的 identity/accepted。
  2. 主口径只收 `identity == "confirmed"` 的图；若合格型号 <10 或留一测试图
     <30，退回 `accepted == True`（confirmed + probable）并在 JSON 标明。
  3. 只保留图片数 >=3 的型号（2 张为下限会单独报告，只作限制说明）。
  4. 留一法：测试图 i 的真型号质心 = 该型号其余 N-1 张图的均值（L2 归一化）；
     其它型号质心用其全部图。余弦相似度取 top-1。指标：top-1 / 机会
     (1/num_models) / balanced accuracy / top-3 / margin / Wilson 95% CI /
     二项检验 / 每型号命中表 / 质心最近邻间隔 / 同家族内 top-1。
  5. 近重复控制：dHash 64bit 同型号参考图 Hamming <= 阈值（默认 8）视为近重复，
     报告命中率，并给出“剔除有近重复参考的测试图”后的准确率敏感性。

输出：
  - `data-test/evals/visual-reference-20261116.json`
  - 不写其它文件；不联网；模型必须已在 HF 本地缓存。

用法：
  PYTHONPATH=src python scripts/probe_visual_reference.py
  PYTHONPATH=src python scripts/probe_visual_reference.py --out tmp/pilot.json

约束：只读 state.json 与图片；只写 --out 指定的新 JSON。数据不足时写
status="insufficient_data" 并以退出码 2 停止，不产出伪造指标。
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

# 必须在 import equiplens.gate（进而 import uform/huggingface_hub）之前生效。
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

# 复用 S2-01 的加载/统计工具（同一份 run glob、去重规则、Wilson/分位数）。
# 用文件路径加载，避免 scripts/ 不是 package 的问题；被导入脚本有 __main__ 保护。
_PVI_PATH = ROOT / "scripts" / "probe_visual_identity.py"
_spec = importlib.util.spec_from_file_location("probe_visual_identity", _PVI_PATH)
pvi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pvi)  # type: ignore[union-attr]

RUN_GLOB = pvi.RUN_GLOB
MIN_IMAGES_PER_MODEL = 3
MIN_MODELS = 10
MIN_TEST_IMAGES = 30
DEFAULT_OUT = "data-test/evals/visual-reference-20261116.json"
DEFAULT_NEAR_DUP_HAMMING = 8  # dHash 64bit：<=8 bit 差异视为同一张图的重压缩/缩放

POLICY_DESCRIPTIONS = {
    "confirmed": "verifications[*].identity == 'confirmed'（标题/型号码命中目标型号）",
    "verified": "verifications[*].accepted == True（confirmed + probable）",
}


# --------------------------------------------------------------------------- #
# 语料
# --------------------------------------------------------------------------- #
def build_identity_index() -> tuple[dict[tuple[str, str], dict], dict[str, dict],
                                    dict[str, dict]]:
    """(run, asset_id) / asset_id -> {identity, accepted} 的资产级聚合。

    一个资产有多个 part 级 verification，identity 在资产内一致；这里仍做聚合，
    优先级 confirmed > probable > unknown，accepted 取任一 True。
    同时返回 asset_id -> {title, url}，用于“同来源/同标题”的近重复分析。
    """
    by_run: dict[tuple[str, str], dict] = {}
    by_asset: dict[str, dict] = {}
    meta_by_asset: dict[str, dict] = {}
    for state_path in sorted(ROOT.glob(RUN_GLOB)):
        run_name = state_path.parent.name
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        for key, info in (state.get("asset_meta") or {}).items():
            if not isinstance(info, dict):
                continue
            asset_id = str(info.get("asset_id") or key)
            if asset_id not in meta_by_asset:
                meta_by_asset[asset_id] = {
                    "title": str(info.get("title") or ""),
                    "url": str(info.get("url") or ""),
                }
        agg: dict[str, dict] = {}
        for key, verif in (state.get("verifications") or {}).items():
            if not isinstance(verif, dict):
                continue
            asset_id = str(key).split(":", 1)[0]
            rec = agg.setdefault(asset_id, {"identities": set(), "accepted": False})
            identity = verif.get("identity")
            if identity:
                rec["identities"].add(str(identity))
            rec["accepted"] = rec["accepted"] or bool(verif.get("accepted"))
        for asset_id, rec in agg.items():
            identities = rec["identities"]
            if "confirmed" in identities:
                identity = "confirmed"
            elif "probable" in identities:
                identity = "probable"
            else:
                identity = "unknown"
            item = {"identity": identity, "accepted": bool(rec["accepted"])}
            by_run[(run_name, asset_id)] = item
            prev = by_asset.get(asset_id)
            # 跨 run 冲突时取更强证据。
            rank = {"unknown": 0, "probable": 1, "confirmed": 2}
            if prev is None or rank[item["identity"]] > rank[prev["identity"]]:
                by_asset[asset_id] = item
    return by_run, by_asset, meta_by_asset


def _policy_keeps(policy: str, rec: dict) -> bool:
    if policy == "confirmed":
        return rec["identity"] == "confirmed"
    if policy == "verified":
        return bool(rec["accepted"])
    raise ValueError(f"unknown policy: {policy}")


def build_corpus(rows: list[dict], by_run: dict, by_asset: dict, asset_meta: dict,
                 policy: str,
                 min_images: int = MIN_IMAGES_PER_MODEL) -> tuple[list[dict], dict]:
    """按 identity 口径过滤，再保留图片数 >= min_images 的型号。"""
    enriched: list[dict] = []
    missing_verification = 0
    filtered_identity = 0
    for row in rows:
        # 同一 asset 可能在 base/sess 两个 run 都出现（同字节、同型号）；identity
        # 规则对标题标点敏感，取两处更强的证据，避免把 confirmed 误降成 unknown。
        rec = by_asset.get(row["asset_id"]) or by_run.get((row["run"], row["asset_id"]))
        if rec is None:
            missing_verification += 1
            continue
        if not _policy_keeps(policy, rec):
            filtered_identity += 1
            continue
        src = asset_meta.get(row["asset_id"], {})
        enriched.append({
            **row,
            "identity": rec["identity"],
            "accepted": rec["accepted"],
            "family": row["category"],
            "title": src.get("title", ""),
            "url": src.get("url", ""),
        })

    counts = Counter(r["model"] for r in enriched)
    kept_models = sorted(m for m, c in counts.items() if c >= min_images)
    kept_set = set(kept_models)
    corpus = [r for r in enriched if r["model"] in kept_set]
    dropped = [
        {"model": m, "n_images": c, "reason": f"below_min_images({min_images})"}
        for m, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        if c < min_images
    ]
    two_image_models = [{"model": m, "n_images": c}
                        for m, c in counts.items() if c == 2]
    meta = {
        "identity_policy": policy,
        "identity_policy_description": POLICY_DESCRIPTIONS[policy],
        "n_pairs_before_identity_filter": len(rows),
        "n_pairs_after_identity_filter": len(enriched),
        "n_filtered_by_identity": filtered_identity,
        "n_missing_verification": missing_verification,
        "n_models_with_images": len(counts),
        "n_models_qualified": len(kept_models),
        "n_images_qualified": len(corpus),
        "n_loo_tests": len(corpus),
        "models": [
            {
                "model": m,
                "family": _model_family(corpus, m),
                "n_images": counts[m],
                "runs": sorted({r["run"] for r in corpus if r["model"] == m}),
            }
            for m in kept_models
        ],
        "dropped_models_below_min": dropped,
        "two_image_models": two_image_models,
    }
    return corpus, meta


def _model_family(corpus: list[dict], model: str) -> str:
    families = sorted({r["family"] for r in corpus if r["model"] == model})
    return families[0] if len(families) == 1 else "mixed"


def qualifies(meta: dict) -> bool:
    return (meta["n_models_qualified"] >= MIN_MODELS
            and meta["n_loo_tests"] >= MIN_TEST_IMAGES)


# --------------------------------------------------------------------------- #
# 图像编码 + 近重复
# --------------------------------------------------------------------------- #
def _unit(vec):
    import numpy as np
    return vec / (float(np.linalg.norm(vec)) + 1e-9)


def encode_corpus(corpus: list[dict], vec_cache: dict[str, object] | None = None
                  ) -> tuple[dict[str, object], list[dict], dict]:
    """对 corpus 里出现的图片编码一次；vec_cache 跨口径复用。"""
    from equiplens import gate

    g = gate._get_gate()
    np, Image = g["np"], g["Image"]
    vecs = vec_cache if vec_cache is not None else {}
    errors: list[dict] = []
    per_model = defaultdict(set)
    t0 = time.time()
    for row in corpus:
        per_model[row["model"]].add(row["asset_id"])
        if row["asset_id"] in vecs:
            continue
        path = ROOT / row["image"]
        try:
            data = path.read_bytes()
            arr = g["ip"](Image.open(io.BytesIO(data)))
            emb = np.asarray(g["ie"].encode(arr, return_features=False)).ravel()
            vecs[row["asset_id"]] = _unit(emb)
        except Exception as exc:  # noqa: BLE001
            errors.append({"asset_id": row["asset_id"], "image": row["image"],
                           "error": str(exc)})
    info = {
        "elapsed_s": round(time.time() - t0, 2),
        "n_unique_images_encoded": len(vecs),
        "read_errors": errors,
        "images_per_model": {m: len(v) for m, v in sorted(per_model.items())},
    }
    return vecs, [r for r in corpus if r["asset_id"] in vecs], info


def dhash64(path: Path) -> int:
    """dHash（9x8 灰度梯度）64bit；对缩放/重压缩不敏感。"""
    import numpy as np
    from PIL import Image

    with Image.open(path) as im:
        gray = im.convert("L").resize((9, 8), Image.BILINEAR)
        arr = np.asarray(gray, dtype=np.int16)
    bits = (arr[:, 1:] > arr[:, :-1]).reshape(-1)
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def hash_corpus(corpus: list[dict]) -> tuple[dict[str, int], dict[str, str], list[dict]]:
    hashes: dict[str, int] = {}
    digests: dict[str, str] = {}
    errors: list[dict] = []
    for row in corpus:
        path = ROOT / row["image"]
        try:
            hashes[row["asset_id"]] = dhash64(path)
            digests[row["asset_id"]] = _md5(path)
        except Exception as exc:  # noqa: BLE001
            errors.append({"asset_id": row["asset_id"], "image": row["image"],
                           "error": str(exc)})
    return hashes, digests, errors


def near_duplicate_map(corpus: list[dict], hashes: dict[str, int],
                       threshold: int) -> dict:
    """每张测试图到“同型号其它参考图”的最小 dHash 距离。"""
    by_model = defaultdict(list)
    for row in corpus:
        by_model[row["model"]].append(row["asset_id"])
    out: dict[str, dict] = {}
    for model, ids in by_model.items():
        for aid in ids:
            others = [hashes[o] for o in ids if o != aid and o in hashes]
            if not others or aid not in hashes:
                continue
            min_h = min((hashes[aid] ^ h).bit_count() for h in others)
            out[aid] = {"min_ref_hamming": min_h, "near_dup": min_h <= threshold}
    return out


# --------------------------------------------------------------------------- #
# 留一评估
# --------------------------------------------------------------------------- #
def evaluate(corpus: list[dict], vecs: dict, near_dup: dict,
             near_dup_threshold: int) -> tuple[list[dict], dict]:
    import numpy as np

    by_model = defaultdict(list)
    for row in corpus:
        by_model[row["model"]].append(row)
    models = sorted(by_model)
    stacks = {m: np.stack([vecs[r["asset_id"]] for r in by_model[m]])
              for m in models}
    full_centroids = {m: _unit(stacks[m].mean(axis=0)) for m in models}

    # 质心两两间隔（参考库本身的可分性）
    centroid_pairs = []
    for m in models:
        best_other, best_cos = None, -1.0
        for other in models:
            if other == m:
                continue
            cos = float(full_centroids[m] @ full_centroids[other])
            if cos > best_cos:
                best_other, best_cos = other, cos
        centroid_pairs.append({
            "model": m,
            "nearest_other_model": best_other,
            "nearest_centroid_cosine": round(best_cos, 4),
            "centroid_separation": round(1.0 - best_cos, 4),
        })

    results: list[dict] = []
    for model in models:
        rows_m = by_model[model]
        for k, row in enumerate(rows_m):
            ref = np.delete(stacks[model], k, axis=0)
            centroids = dict(full_centroids)
            centroids[model] = _unit(ref.mean(axis=0))
            test_vec = vecs[row["asset_id"]]
            sims = {m: float(test_vec @ centroids[m]) for m in models}
            ranked = sorted(sims.items(), key=lambda kv: (-kv[1], kv[0]))
            predicted, _ = ranked[0]
            sim_true = sims[model]
            best_other_model, best_other_sim = max(
                ((m, s) for m, s in sims.items() if m != model),
                key=lambda kv: (kv[1], kv[0]),
            )
            margin = sim_true - best_other_sim
            rank = 1 + sum(1 for m, s in sims.items() if m != model and s > sim_true)
            nd = near_dup.get(row["asset_id"], {})
            same_title_ref = any(
                o.get("title") and o["title"] == row.get("title")
                for j, o in enumerate(rows_m) if j != k)
            results.append({
                "asset_id": row["asset_id"],
                "image": row["image"],
                "run": row["run"],
                "family": row["family"],
                "view": row.get("view"),
                "scene": row.get("scene"),
                "title": row.get("title", ""),
                "width": row.get("width"),
                "height": row.get("height"),
                "model": model,
                "identity": row["identity"],
                "n_model_images": len(rows_m),
                "predicted_model": predicted,
                "predicted_family": _model_family(corpus, predicted),
                "sim_true": round(sim_true, 4),
                "sim_best_other": round(best_other_sim, 4),
                "best_other_model": best_other_model,
                "margin": round(margin, 4),
                "rank_of_true": rank,
                "correct": predicted == model,
                "top3_correct": rank <= 3,
                "near_dup_to_reference": bool(nd.get("near_dup", False)),
                "min_ref_hamming": nd.get("min_ref_hamming"),
                "same_title_reference": same_title_ref,
                "_sims": sims,  # 内部用，写 JSON 前丢弃
            })

    # 同家族内 top-1（候选只保留同 family 的型号）：更接近真实“同品类选型”
    families = defaultdict(list)
    for row in corpus:
        families[row["family"]].append(row)
    within_family = {}
    for family, rows_f in sorted(families.items()):
        fam_models = sorted({r["model"] for r in rows_f})
        if len(fam_models) < 2:
            continue
        subset = [r for r in results if r["family"] == family]
        hits = 0
        for r in subset:
            pred = max(fam_models, key=lambda m: (r["_sims"][m], m))
            hits += int(pred == r["model"])
        within_family[family] = {
            "n_models": len(fam_models),
            "n_test": len(subset),
            "top1": round(hits / len(subset), 4) if subset else None,
            "chance": round(1.0 / len(fam_models), 4),
            "accuracy_vs_chance_lift": round(
                (hits / len(subset)) / (1.0 / len(fam_models)), 4) if subset else None,
        }

    meta = {
        "models": models,
        "full_centroids": full_centroids,
        "images_per_model": {m: len(by_model[m]) for m in models},
        "centroid_pairwise": centroid_pairs,
        "within_family": within_family,
        "within_model_cohesion": pvi._percentiles(
            [float(e @ full_centroids[m]) for m in models for e in stacks[m]]),
        "centroid_to_global_cosine": {
            m: round(float(full_centroids[m] @ _unit(
                np.concatenate([stacks[x] for x in models]).mean(axis=0))), 4)
            for m in models
        },
    }
    return results, meta


def _binomial_p_two_sided(k: int, n: int, p: float) -> float:
    if n <= 0:
        return 1.0
    pmf = [math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(n + 1)]
    obs = pmf[k]
    value = min(1.0, sum(v for v in pmf if v <= obs * (1 + 1e-12)))
    return float(f"{value:.3g}")  # 避免把 1e-21 四舍五入成 0.0


def _stats(values: list[float]) -> dict:
    return pvi._percentiles(values)


def summarize(results: list[dict], eval_meta: dict,
              near_dup_threshold: int, elapsed: float,
              read_errors: list[dict]) -> dict:
    models = eval_meta["models"]
    n = len(results)
    hits = sum(1 for r in results if r["correct"])
    top3 = sum(1 for r in results if r["top3_correct"])
    accuracy = hits / n if n else 0.0
    chance = 1.0 / len(models) if models else 0.0

    per_model: list[dict] = []
    predicted_counts = Counter(r["predicted_model"] for r in results)
    absorbed = Counter(r["predicted_model"] for r in results if not r["correct"])
    for model in models:
        rows_m = [r for r in results if r["model"] == model]
        m_hits = sum(1 for r in rows_m if r["correct"])
        confusions = Counter(r["predicted_model"] for r in rows_m if not r["correct"])
        cent = next(c for c in eval_meta["centroid_pairwise"] if c["model"] == model)
        per_model.append({
            "model": model,
            "family": _model_family(
                [{"model": r["model"], "family": r["family"]} for r in results], model),
            "n_images": eval_meta["images_per_model"][model],
            "n_test": len(rows_m),
            "hits": m_hits,
            "accuracy": round(m_hits / len(rows_m), 4) if rows_m else None,
            "accuracy_wilson95": pvi._wilson(m_hits, len(rows_m)),
            "mean_margin": round(sum(r["margin"] for r in rows_m) / len(rows_m), 4)
            if rows_m else None,
            "min_margin": min((r["margin"] for r in rows_m), default=None),
            "max_margin": max((r["margin"] for r in rows_m), default=None),
            "n_unique_titles": len({r.get("title") for r in rows_m if r.get("title")}),
            "times_predicted": predicted_counts[model],
            "absorbed_from_other_models": absorbed[model],
            "nearest_centroid": {
                "model": cent["nearest_other_model"],
                "cosine": cent["nearest_centroid_cosine"],
                "separation": cent["centroid_separation"],
            },
            "confused_with": [
                {"predicted_model": p, "count": c}
                for p, c in confusions.most_common()
            ],
        })

    per_model_acc = [p["accuracy"] for p in per_model if p["accuracy"] is not None]
    balanced = sum(per_model_acc) / len(per_model_acc) if per_model_acc else 0.0
    largest_class = max((p["n_test"] for p in per_model), default=0)
    majority = largest_class / n if n else 0.0

    margins = [r["margin"] for r in results]
    margin_correct = [r["margin"] for r in results if r["correct"]]
    margin_wrong = [r["margin"] for r in results if not r["correct"]]

    # 错误结构：家族内错 vs 跨家族错
    errors = [r for r in results if not r["correct"]]
    cross_family = [r for r in errors if r["family"] != r["predicted_family"]]
    confusion_pairs = Counter((r["model"], r["predicted_model"]) for r in errors)

    # 近重复敏感性
    flagged = [r for r in results if r["near_dup_to_reference"]]
    clean = [r for r in results if not r["near_dup_to_reference"]]
    exact_dup_groups = eval_meta.get("exact_dup_groups", [])
    flagged_exact = {aid for group in exact_dup_groups for aid in group}
    clean_strict = [r for r in results if r["asset_id"] not in flagged_exact]

    # 同标题参考：同型号内 title 完全相同，很可能同一网页/同一台车（非严格同车判定）
    same_title = [r for r in results if r.get("same_title_reference")]
    clean_title = [r for r in results if not r.get("same_title_reference")]
    all_titles = {r.get("title") for r in results if r.get("title")}
    models_single_title = [
        p["model"] for p in per_model
        if p["n_unique_titles"] == 1 and p["n_test"] >= 3
    ]

    by_view: dict[str, dict] = {}
    for view in sorted({str(r.get("view")) for r in results}):
        subset = [r for r in results if str(r.get("view")) == view]
        by_view[view] = {
            "n": len(subset),
            "top1": round(sum(1 for r in subset if r["correct"]) / len(subset), 4),
        }
    by_family: dict[str, dict] = {}
    for family in sorted({r["family"] for r in results}):
        subset = [r for r in results if r["family"] == family]
        by_family[family] = {
            "n": len(subset),
            "n_models": len({r["model"] for r in subset}),
            "top1": round(sum(1 for r in subset if r["correct"]) / len(subset), 4),
        }

    return {
        "n_test": n,
        "n_models": len(models),
        "overall_top1": round(accuracy, 4),
        "overall_top1_wilson95": pvi._wilson(hits, n),
        "chance_uniform": round(chance, 4),
        "accuracy_vs_chance_lift": round(accuracy / chance, 3) if chance else None,
        "binomial_p_vs_chance": _binomial_p_two_sided(hits, n, chance),
        "balanced_accuracy": round(balanced, 4),
        "balanced_accuracy_vs_chance_lift": round(balanced / chance, 3) if chance else None,
        "majority_class_baseline": round(majority, 4),
        "top3_accuracy": round(top3 / n, 4) if n else None,
        "top3_chance_uniform": round(min(3.0 / len(models), 1.0), 4) if models else None,
        "centroid_margins": {
            "note": "margin = cos(test, true LOO centroid) - max cos(test, 其它型号质心)",
            "all": _stats(margins),
            "correct": _stats(margin_correct),
            "incorrect": _stats(margin_wrong),
            "positive_rate": round(sum(1 for m in margins if m > 0) / n, 4) if n else None,
        },
        "centroid_pairwise": eval_meta["centroid_pairwise"],
        "min_centroid_separation": min(
            (c["centroid_separation"] for c in eval_meta["centroid_pairwise"]),
            default=None),
        "within_model_cohesion": eval_meta["within_model_cohesion"],
        "centroid_to_global_cosine": eval_meta["centroid_to_global_cosine"],
        "hubness": {
            "note": ("被预测次数远高于自身测试数 = hub（质心靠近全局均值，"
                     "会把别的型号吸过来）"),
            "top_absorbers": [
                {"model": m, "absorbed_from_other_models": absorbed[m],
                 "times_predicted": predicted_counts[m]}
                for m in sorted(models, key=lambda x: (-absorbed[x], x))[:5]
            ],
        },
        "within_family": eval_meta["within_family"],
        "by_family": by_family,
        "by_view": by_view,
        "errors": {
            "n_errors": len(errors),
            "cross_family_errors": len(cross_family),
            "cross_family_share_of_errors": round(len(cross_family) / len(errors), 4)
            if errors else None,
            "models_with_zero_hits": [p["model"] for p in per_model if p["hits"] == 0],
            "top_confusion_pairs": [
                {"true_model": t, "predicted_model": p, "count": c}
                for (t, p), c in confusion_pairs.most_common(10)
            ],
        },
        "near_duplicate_control": {
            "method": f"dHash 64bit 同型号参考图 Hamming <= {near_dup_threshold} 视为近重复",
            "threshold_hamming": near_dup_threshold,
            "n_flagged_test_images": len(flagged),
            "flagged_asset_ids": sorted(r["asset_id"] for r in flagged),
            "accuracy_excluding_flagged": round(
                sum(1 for r in clean if r["correct"]) / len(clean), 4) if clean else None,
            "n_after_excluding_flagged": len(clean),
            "exact_duplicate_groups": exact_dup_groups,
            "accuracy_excluding_exact_duplicate_tests": round(
                sum(1 for r in clean_strict if r["correct"]) / len(clean_strict), 4)
            if clean_strict else None,
            "n_after_excluding_exact": len(clean_strict),
            "same_source_title_control": {
                "note": ("同型号参考图与测试图 title 完全相同 = 很可能同一网页/同一台车；"
                         "这是来源相关代理，不是严格的同车判定"),
                "n_images_with_same_title_reference": len(same_title),
                "accuracy_excluding_same_title": round(
                    sum(1 for r in clean_title if r["correct"]) / len(clean_title), 4)
                if clean_title else None,
                "n_after_excluding_same_title": len(clean_title),
                "source_diversity": {
                    "n_images": n,
                    "n_unique_titles": len(all_titles),
                    "models_all_images_same_title": models_single_title,
                },
            },
        },
        "per_model": per_model,
        "elapsed_s": elapsed,
        "read_errors": read_errors,
    }


def _decision(metrics: dict) -> dict:
    """按预先写死的门槛给接线结论（可复现，不事后拟合）。

    研究结论（能否分型号）和工程结论（能否接进 VERIFY）分开：一个机制可以
    显著优于随机，但绝对准确率/margin 还不足以当 VERIFY 的证据门槛。
    """
    top1 = metrics["overall_top1"]
    macro = metrics["balanced_accuracy"]
    lift = metrics["accuracy_vs_chance_lift"] or 0.0
    clean = metrics["near_duplicate_control"]["accuracy_excluding_flagged"] or 0.0
    if top1 >= 0.75 and macro >= 0.70 and clean >= 0.70:
        wiring = "go"
        headline = "参考图库有接近可用的身份分辨力，可进入 VERIFY 接线设计"
    elif top1 >= 0.40 and macro >= 0.35 and lift >= 5.0:
        wiring = "no-go-now"
        headline = ("信号真实存在，但绝对准确率/margin 不足以接 VERIFY；"
                    "先离线建库、扩数据再评估")
    else:
        wiring = "no-go"
        headline = "没有可用身份分辨力，不接线"
    return {
        "wiring_into_verify": wiring,
        "research_verdict": (
            "positive: image-to-image 明显优于零样本文本"
            if lift >= 5.0 and top1 >= 0.40 else
            "negative: 没有明显优于随机的身份信号"
        ),
        "offline_library_build": (
            "conditional-go: 先攒参考图并做 run-disjoint 验证，不接生产"
            if wiring == "no-go-now" else
            ("go: 可先建离线库" if wiring == "go" else "no-go")
        ),
        "headline": headline,
        "thresholds": {
            "wire_go": "top1>=0.75 且 balanced>=0.70 且 去近重复 top1>=0.70",
            "offline_conditional_go": "top1>=0.40 且 balanced>=0.35 且 lift>=5x",
            "else": "no-go",
        },
        "rationale": [
            f"top-1 {top1:.1%} vs 机会 {metrics['chance_uniform']:.1%}（{lift:.1f}x），"
            f"95% CI {metrics['overall_top1_wilson95']}",
            f"balanced accuracy {macro:.1%}，majority baseline "
            f"{metrics['majority_class_baseline']:.1%}",
            f"去近重复测试集 top-1 {clean:.1%}",
            f"top-3 {metrics['top3_accuracy']:.1%} vs 机会 "
            f"{metrics['top3_chance_uniform']:.1%}",
            f"二项检验 p={metrics['binomial_p_vs_chance']:g}",
        ],
    }


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="S2-06 image-to-image 参考图库探针")
    ap.add_argument("--out", default=DEFAULT_OUT, help="输出 JSON 路径")
    ap.add_argument("--min-images-per-model", type=int, default=MIN_IMAGES_PER_MODEL)
    ap.add_argument("--near-dup-hamming", type=int, default=DEFAULT_NEAR_DUP_HAMMING)
    args = ap.parse_args(argv)

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows, runs_used, problems = pvi.collect_assets()
    by_run, by_asset, asset_meta = build_identity_index()
    identity_counts = Counter(
        (by_asset.get(r["asset_id"])
         or by_run.get((r["run"], r["asset_id"])) or {"identity": "missing"})["identity"]
        for r in rows
    )
    print(f"扫描 {len(rows)} 个 image+model 资产，{len(runs_used)} 个 run；"
          f"identity={dict(identity_counts)}")
    if problems:
        print("警告:", *problems, sep="\n  ")

    confirmed, confirmed_meta = build_corpus(
        rows, by_run, by_asset, asset_meta, "confirmed", args.min_images_per_model)
    verified, verified_meta = build_corpus(
        rows, by_run, by_asset, asset_meta, "verified", args.min_images_per_model)
    primary_policy = "confirmed" if qualifies(confirmed_meta) else "verified"
    primary_corpus = confirmed if primary_policy == "confirmed" else verified
    primary_meta = confirmed_meta if primary_policy == "confirmed" else verified_meta
    fallback_used = primary_policy != "confirmed"

    corpus_block = {
        "source": "data-test/runs/m43-*/state.json (asset_meta + verifications)",
        "n_pairs_total": len(rows),
        "n_runs": len(runs_used),
        "runs_used": runs_used,
        "identity_counts": dict(sorted(identity_counts.items())),
        "primary_policy": primary_policy,
        "fallback_to_verified": fallback_used,
        "min_images_per_model": args.min_images_per_model,
        "min_models_required": MIN_MODELS,
        "min_test_images_required": MIN_TEST_IMAGES,
        "confirmed": confirmed_meta,
        "verified": verified_meta,
    }

    if not qualifies(primary_meta):
        payload = {
            "probe": "visual-reference-library",
            "status": "insufficient_data",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "reason": (f"qualified models {primary_meta['n_models_qualified']} "
                       f"< {MIN_MODELS} or LOO tests "
                       f"{primary_meta['n_loo_tests']} < {MIN_TEST_IMAGES}"),
            "corpus": corpus_block,
            "problems": problems,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        print(f"数据不足：{payload['reason']}；已写 {args.out}，退出。")
        return 2

    print(f"主口径={primary_policy}：{primary_meta['n_images_qualified']} 图 / "
          f"{primary_meta['n_models_qualified']} 型号 / "
          f"{primary_meta['n_loo_tests']} 张留一测试图")

    t0 = time.time()
    vec_cache: dict[str, object] = {}
    vecs, encoded_rows, enc_info = encode_corpus(primary_corpus, vec_cache)
    if len(encoded_rows) < len(primary_corpus):
        print(f"警告：{len(primary_corpus) - len(encoded_rows)} 张图读取失败，已剔除")
    hashes, digests, hash_errors = hash_corpus(encoded_rows)
    hash_groups = defaultdict(list)
    for aid, digest in digests.items():
        hash_groups[digest].append(aid)
    exact_dup_groups = [sorted(v) for v in hash_groups.values() if len(v) > 1]
    near_dup = near_duplicate_map(encoded_rows, hashes, args.near_dup_hamming)

    results, eval_meta = evaluate(encoded_rows, vecs, near_dup, args.near_dup_hamming)
    eval_meta["exact_dup_groups"] = exact_dup_groups
    elapsed = round(time.time() - t0, 2)
    metrics = summarize(results, eval_meta, args.near_dup_hamming,
                        elapsed, enc_info["read_errors"])

    # 敏感性：另一 identity 口径（confirmed <-> verified）
    sensitivity = None
    other_policy = "verified" if primary_policy == "confirmed" else "confirmed"
    other_corpus = verified if other_policy == "verified" else confirmed
    other_meta = verified_meta if other_policy == "verified" else confirmed_meta
    if qualifies(other_meta):
        print(f"敏感性口径={other_policy}：{other_meta['n_images_qualified']} 图 / "
              f"{other_meta['n_models_qualified']} 型号")
        o_vecs, o_rows, o_enc = encode_corpus(other_corpus, vec_cache)
        o_hashes, o_digests, _ = hash_corpus(o_rows)
        o_near = near_duplicate_map(o_rows, o_hashes, args.near_dup_hamming)
        o_results, o_eval = evaluate(o_rows, o_vecs, o_near, args.near_dup_hamming)
        o_metrics = summarize(o_results, o_eval, args.near_dup_hamming,
                              o_enc["elapsed_s"], o_enc["read_errors"])
        sensitivity = {
            "identity_policy": other_policy,
            "description": POLICY_DESCRIPTIONS[other_policy],
            "n_images": other_meta["n_images_qualified"],
            "n_models": other_meta["n_models_qualified"],
            "n_test": o_metrics["n_test"],
            "overall_top1": o_metrics["overall_top1"],
            "chance_uniform": o_metrics["chance_uniform"],
            "accuracy_vs_chance_lift": o_metrics["accuracy_vs_chance_lift"],
            "balanced_accuracy": o_metrics["balanced_accuracy"],
            "binomial_p_vs_chance": o_metrics["binomial_p_vs_chance"],
            "accuracy_excluding_near_dup": o_metrics["near_duplicate_control"][
                "accuracy_excluding_flagged"],
            "per_model": o_metrics["per_model"],
            "top_failures": [
                {k: r[k] for k in ("asset_id", "model", "predicted_model", "margin",
                                    "run", "image")}
                for r in sorted(o_results, key=lambda r: r["margin"])[:10]
                if not r["correct"]
            ],
        }

    # 逐测试行落 JSON（去掉内部 sims）
    public_rows = [{k: v for k, v in r.items() if k != "_sims"} for r in results]
    failures = sorted(
        [r for r in public_rows if not r["correct"]],
        key=lambda r: (r["margin"], r["model"]),
    )
    recommendation = _decision(metrics)
    per_model = metrics.pop("per_model")

    payload = {
        "probe": "visual-reference-library",
        "status": "ok",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "task": "S2-06",
        "question": ("image-to-image 每型号参考图库能否比零样本文本标签更好地"
                     "区分型号身份？"),
        "model": {
            "name": "unum-cloud/uform3-image-text-english-small",
            "backend": "UForm3 ONNX (CPU) via src/equiplens/gate.py",
            "image_embed_dim": 256,
            "preprocessing": "gate._get_gate()['ip'] / ['ie']，与门卫同一权重",
        },
        "method": {
            "image": "UForm3 image encoder，单位向量，余弦相似度",
            "prototype": "每型号参考图均值向量，L2 归一化",
            "leave_one_out": ("测试图 i 的真型号质心 = 该型号其余 N-1 张图的均值；"
                              "其它型号质心用其全部图；top-1 over 全部合格型号"),
            "candidates": "只含图片数 >= min_images_per_model 的型号（主结果 15 个）",
            "chance": "1 / num_candidate_models",
            "identity_primary": POLICY_DESCRIPTIONS[primary_policy],
            "identity_fallback": ("confirmed 合格数不足时退回 accepted，并在 JSON 写明"
                                  if fallback_used else "未使用（confirmed 已满足门槛）"),
            "text_baseline": "跳过：文本标签已在 S2-01 测过（3 选 1 11.0% vs 33.3%）",
            "near_duplicate": f"dHash 64bit，同型号参考 Hamming <= "
                              f"{args.near_dup_hamming} 视为近重复",
            "within_family": "候选限制在同 family（desert/forklift/roller/wrecker/sweeper）内",
            "binomial_test": "精确二项双侧检验，H0: top1 == 1/num_models",
        },
        "corpus": corpus_block,
        "metrics": metrics,
        "per_model": per_model,
        "failures": failures,
        "sensitivity_other_identity_policy": sensitivity,
        "recommendation": recommendation,
        "rows": public_rows,
        "problems": problems,
        "hash_read_errors": hash_errors,
    }

    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(out_path)

    print(f"N={metrics['n_test']}  models={metrics['n_models']}  "
          f"top1={metrics['overall_top1']:.3f}  chance={metrics['chance_uniform']:.3f}  "
          f"lift={metrics['accuracy_vs_chance_lift']:.1f}x  "
          f"macro={metrics['balanced_accuracy']:.3f}  p={metrics['binomial_p_vs_chance']:g}")
    print(f"margin median={metrics['centroid_margins']['all'].get('median')}  "
          f"min_centroid_sep={metrics['min_centroid_separation']}  "
          f"near_dup_flagged={metrics['near_duplicate_control']['n_flagged_test_images']}")
    print(f"wiring={recommendation['wiring_into_verify']}  "
          f"research={recommendation['research_verdict']} -> {args.out}  "
          f"(total {time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
