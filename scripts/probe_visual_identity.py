# -*- coding: utf-8 -*-
"""S2-01 可行性探针：本地 CLIP 能否在文本之外提供“视觉身份”证据。

问题：VERIFY 现在只有文本侧证据（标题/型号/规则）。把已落盘的候选图喂给项目
现成的 UForm3 零样本模型（`src/equiplens/gate.py`，与门卫同一个本地 ONNX 权重），
比较“真型号 / 随机另一型号 / 泛化 truck”三个文本候选的余弦相似度，看真型号能否
稳定 top-1。若不能，就不值得把视觉身份接进 VERIFY。

方法（全部离线、无 LLM、无新模型下载）：
  1. 扫描 `data-test/runs/m43-*/state.json`，取 `asset_meta` 中
     `model` 非空、且 `images/<目录>/<asset_id>.jpg` 真实存在的资产；
     按 asset_id 去重（base 批次优先于 sess 批次），并要求 >=30 对。
  2. 对每张图编码一次；文本候选三种：
       true   = "a photo of a {asset_meta.model}"      （标签源：state.json）
       random = "a photo of a {随机另一 model}"         （固定种子，可复现）
       truck  = "a photo of a truck"                    （泛化对照）
     另加一组同批（同 run/同类目代理）随机型号作为更严格的对照。
  3. 指标：3 选 1 top-1 准确率（true 排名第一）、true-vs-random 二选一准确率、
     truck 夺魁率、margin 分布（true 与最强对照的差）、场景/脚本/验收子集拆分。
     另做“文本先验”对照：把标签对本语料的留一平均相似度减掉，排除
     “某标签天生更贴这类图”的文本偏置后再看成对胜负。

输出：默认 `data-test/evals/visual-identity-20261116.json`（含逐资产分与汇总）。

用法：
  PYTHONPATH=src python scripts/probe_visual_identity.py
  PYTHONPATH=src python scripts/probe_visual_identity.py --limit 50   # 试跑

约束：只读 state.json 与图片；只写 --out 指定的新 JSON。不联网：
进程启动即设置 HF_HUB_OFFLINE=1，模型必须已在本地缓存，否则直接失败。
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import random
import sys
import time
from pathlib import Path

# 必须在 import equiplens.gate（进而 import uform/huggingface_hub）之前生效。
# 强制离线：探针不允许联网/下载模型，权重必须已在 HF 缓存里。
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

RUN_GLOB = "data-test/runs/m43-*/state.json"
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
MIN_PAIRS = 30
DEFAULT_OUT = "data-test/evals/visual-identity-20261116.json"
TRUCK_LABEL = "a photo of a truck"
LABEL_TEMPLATE = "a photo of a {}"
CATEGORY_SUFFIXES = ("desert", "forklift", "roller", "wrecker", "sweeper")


# --------------------------------------------------------------------------- #
# 语料收集
# --------------------------------------------------------------------------- #
def _category(run_name: str) -> str:
    """用 run 目录后缀当“类目代理”（m43-base-c1-desert → desert）。"""
    for suffix in CATEGORY_SUFFIXES:
        if run_name.endswith(suffix):
            return suffix
    return "unknown"


def _normalize_label(label: str) -> str:
    """只用于判重/排除“同名不同写法”，不做语义归一。"""
    return "".join(ch for ch in label.lower() if ch.isalnum())


def _has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _label_script(label: str) -> str:
    """标签脚本：cjk（含中文）或 latin_only（纯拉丁/数字）。"""
    return "cjk" if _has_cjk(label) else "latin_only"


def _image_index(run_dir: Path) -> dict[str, Path]:
    """asset_id（文件名主干）→ 图片路径。"""
    index: dict[str, Path] = {}
    images_dir = run_dir / "images"
    if not images_dir.is_dir():
        return index
    for path in images_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            index.setdefault(path.stem, path)
    return index


def collect_assets(run_glob: str = RUN_GLOB) -> tuple[list[dict], list[str], list[str]]:
    """返回 (rows, runs_used, problems)。只保留图片存在且 model 非空的资产。"""
    rows: list[dict] = []
    seen: set[str] = set()
    runs_used: list[str] = []
    problems: list[str] = []
    for state_path in sorted(ROOT.glob(run_glob)):
        run_dir = state_path.parent
        run_name = run_dir.name
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{run_name}: state.json 读取失败: {exc}")
            continue
        meta = state.get("asset_meta") or {}
        if not isinstance(meta, dict):
            problems.append(f"{run_name}: asset_meta 不是 dict，跳过")
            continue
        images = _image_index(run_dir)
        accepted_ids: set[str] = set()
        for key, verif in (state.get("verifications") or {}).items():
            if isinstance(verif, dict) and verif.get("accepted"):
                accepted_ids.add(str(key).split(":", 1)[0])
        accepted_targets: set[str] = set()
        for unit in (state.get("units") or {}).values():
            if isinstance(unit, dict):
                for target in unit.get("accepted_targets") or []:
                    accepted_targets.add(str(target).strip())

        kept = 0
        for key, info in meta.items():
            if not isinstance(info, dict):
                continue
            asset_id = str(info.get("asset_id") or key)
            model = str(info.get("model") or "").strip()
            image = images.get(asset_id) or images.get(str(key))
            if not model or image is None:
                continue
            if asset_id in seen:  # base 先于 sess（排序保证），不重复计数
                continue
            seen.add(asset_id)
            try:
                rel = image.relative_to(ROOT).as_posix()
            except ValueError:
                rel = str(image)
            rows.append({
                "asset_id": asset_id,
                "run": run_name,
                "category": _category(run_name),
                "image": rel,
                "model": model,
                "label_source": "state.json asset_meta[*].model",
                "label_script": _label_script(model),
                "scene": info.get("scene"),
                "view": info.get("view"),
                "query_tier": info.get("query_tier"),
                "width": info.get("width"),
                "height": info.get("height"),
                "accepted_any": asset_id in accepted_ids,
                "accepted_model": model in accepted_targets,
            })
            kept += 1
        if kept:
            runs_used.append(run_name)
    return rows, runs_used, problems


# --------------------------------------------------------------------------- #
# 打分
# --------------------------------------------------------------------------- #
def _pick_other(true_label: str, pool: list[str], seed: str) -> str | None:
    """从 pool 里用稳定种子选一个与真标签不同名的型号。"""
    norm = _normalize_label(true_label)
    candidates = [m for m in pool if _normalize_label(m) != norm]
    if not candidates:
        return None
    return random.Random(seed).choice(candidates)


def _percentiles(values: list[float]) -> dict:
    if not values:
        return {}
    import numpy as np

    arr = np.asarray(values, dtype=float)
    p = {f"p{q}": round(float(np.percentile(arr, q)), 4) for q in (10, 25, 50, 75, 90)}
    return {
        "mean": round(float(arr.mean()), 4),
        "median": round(float(np.median(arr)), 4),
        "min": round(float(arr.min()), 4),
        "max": round(float(arr.max()), 4),
        **p,
    }


def _wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def run_probe(rows: list[dict], limit: int = 0) -> tuple[list[dict], dict]:
    """编码图片 + 文本候选，返回 (逐资产结果, 运行信息)。

    两遍处理：先把所有图编码成单位向量，再去重编码文本候选、一次矩阵乘。
    顺带算“文本先验”（某标签对本语料的平均相似度），用于检验成对胜负是
    图像证据还是“标签文本天生更贴这张图”的偏置（见 prior-corrected 指标）。
    """
    from equiplens import gate  # 延迟 import：此时离线环境变量已生效

    g = gate._get_gate()
    np, Image, text_emb = g["np"], g["Image"], g["text_emb"]

    # 候选池用完整语料，保证 --limit 试跑时随机对照仍然来自全集。
    pool = sorted({r["model"] for r in rows})
    by_run: dict[str, list[str]] = {}
    for r in rows:
        by_run.setdefault(r["run"], []).append(r["model"])
    by_run = {k: sorted(set(v)) for k, v in by_run.items()}

    if limit:
        rows = rows[:limit]

    t0 = time.time()
    encoded: list[tuple[dict, object]] = []
    read_errors: list[dict] = []
    for i, row in enumerate(rows, 1):
        path = ROOT / row["image"]
        try:
            data = path.read_bytes()
            arr = g["ip"](Image.open(io.BytesIO(data)))
            emb = np.asarray(g["ie"].encode(arr, return_features=False)).ravel()
            emb = emb / (np.linalg.norm(emb) + 1e-9)
        except Exception as exc:  # noqa: BLE001
            read_errors.append({"asset_id": row["asset_id"], "image": row["image"],
                                "error": str(exc)})
            continue
        encoded.append((row, emb))
        if i % 50 == 0:
            print(f"  ... {i}/{len(rows)}  image encode ok, {time.time() - t0:.1f}s")

    # 候选标签计划（固定种子，可复现）
    plan: list[dict] = []
    for pos, (row, _) in enumerate(encoded):
        rand_label = _pick_other(row["model"], pool, f"{row['asset_id']}|random")
        if rand_label is None:
            continue
        same_label = _pick_other(row["model"], by_run.get(row["run"], []),
                                 f"{row['asset_id']}|same")
        plan.append({"pos": pos, "row": row, "random": rand_label, "same": same_label})

    def _texts(row: dict, rand_label: str, same_label: str | None) -> dict[str, str]:
        out = {
            "true": LABEL_TEMPLATE.format(row["model"]),
            "random": LABEL_TEMPLATE.format(rand_label),
            "truck": TRUCK_LABEL,
        }
        if same_label is not None:
            out["random_same_category"] = LABEL_TEMPLATE.format(same_label)
        return out

    # 文本去重后一次编码
    all_texts = {TRUCK_LABEL}
    for item in plan:
        all_texts.update(_texts(item["row"], item["random"], item["same"]).values())
    text_list = sorted(all_texts)
    t_index = {t: i for i, t in enumerate(text_list)}
    text_mat = np.stack([text_emb(t) for t in text_list])  # (m, 256)
    embs = np.stack([e for _, e in encoded])              # (n, 256)
    sim_mat = embs @ text_mat.T                            # (n, m)
    col_sum = sim_mat.sum(axis=0)
    n = len(embs)

    def _loo_prior(idx: int, sim: float) -> float:
        """留一先验：该文本标签对语料其余图的平均相似度。"""
        return float((col_sum[idx] - sim) / max(n - 1, 1))

    out: list[dict] = []
    for item in plan:
        row, rand_label, same_label = item["row"], item["random"], item["same"]
        texts = _texts(row, rand_label, same_label)
        idx = {k: t_index[t] for k, t in texts.items()}
        raw = {k: float(sim_mat[item["pos"], i]) for k, i in idx.items()}
        sims = {k: round(v, 4) for k, v in raw.items()}
        prior = {k: round(_loo_prior(idx[k], raw[k]), 4) for k in raw}
        corrected = {k: round(raw[k] - prior[k], 4) for k in raw}

        sim_true, sim_random, sim_truck = raw["true"], raw["random"], raw["truck"]
        top1 = max(("true", "random", "truck"), key=lambda k: raw[k])
        corrected_top1 = max(("true", "random", "truck"), key=lambda k: corrected[k])
        same = raw.get("random_same_category")
        same_prior = prior.get("random_same_category")
        out.append({
            **row,
            "random_model": rand_label,
            "random_same_category_model": same_label,
            "candidates": texts,
            "sims": sims,
            "text_prior_loo": prior,
            "sims_prior_corrected": corrected,
            "top1": top1,
            "top1_prior_corrected": corrected_top1,
            "correct_top1": top1 == "true",
            "correct_pairwise": sim_true > sim_random,
            "correct_top1_prior_corrected": corrected_top1 == "true",
            "correct_pairwise_prior_corrected": corrected["true"] > corrected["random"],
            "correct_pairwise_same_category": (sim_true > same) if same is not None else None,
            "margin_top1": round(sim_true - max(sim_random, sim_truck), 4),
            "margin_pairwise": round(sim_true - sim_random, 4),
            "margin_pairwise_prior_corrected": round(corrected["true"] - corrected["random"], 4),
            "margin_pairwise_same_category": (round(sim_true - same, 4)
                                              if same_prior is not None else None),
        })

    elapsed = round(time.time() - t0, 2)
    return out, {"elapsed_s": elapsed, "read_errors": read_errors,
                 "n_text_labels": len(text_list)}


def summarize(rows: list[dict], n_models: int, n_runs: int, elapsed: float,
              read_errors: list[dict], model_name: str, n_text_labels: int = 0) -> dict:
    n = len(rows)
    correct = sum(1 for r in rows if r["correct_top1"])
    pairwise = sum(1 for r in rows if r["correct_pairwise"])
    prior_correct = sum(1 for r in rows if r["correct_top1_prior_corrected"])
    prior_pairwise = sum(1 for r in rows if r["correct_pairwise_prior_corrected"])
    truck_wins = sum(1 for r in rows if r["top1"] == "truck")
    same_rows = [r for r in rows if r["correct_pairwise_same_category"] is not None]
    same_correct = sum(1 for r in same_rows if r["correct_pairwise_same_category"])

    model_cat = {r["model"]: r["category"] for r in rows}
    cross_cat_rows = [r for r in rows if model_cat.get(r["random_model"]) != r["category"]]
    same_cat_rows = [r for r in rows if model_cat.get(r["random_model"]) == r["category"]]

    def block(subset: list[dict]) -> dict:
        if not subset:
            return {"n": 0}
        c = sum(1 for r in subset if r["correct_top1"])
        p = sum(1 for r in subset if r["correct_pairwise"])
        cp = sum(1 for r in subset if r["correct_top1_prior_corrected"])
        pp = sum(1 for r in subset if r["correct_pairwise_prior_corrected"])
        t = sum(1 for r in subset if r["top1"] == "truck")
        return {
            "n": len(subset),
            "n_models": len({r["model"] for r in subset}),
            "accuracy_3way": round(c / len(subset), 4),
            "accuracy_pairwise": round(p / len(subset), 4),
            "accuracy_3way_prior_corrected": round(cp / len(subset), 4),
            "accuracy_pairwise_prior_corrected": round(pp / len(subset), 4),
            "truck_top1_rate": round(t / len(subset), 4),
            "margin_top1_median": _percentiles([r["margin_top1"] for r in subset]).get("median"),
        }

    def group(field: str) -> dict:
        buckets: dict[str, list[dict]] = {}
        for r in rows:
            buckets.setdefault(str(r.get(field)), []).append(r)
        return {k: block(v) for k, v in sorted(buckets.items())}

    # 同一型号只留一张图（去相关检查）
    one_per_model: dict[str, dict] = {}
    for r in rows:
        one_per_model.setdefault(r["model"], r)
    one_per_model_rows = list(one_per_model.values())

    # 每个型号的成对胜负是否“清一色”——若几乎全是全对/全错，说明胜负更像
    # 标签文本的固定偏置，而不是逐图证据。
    per_model_wins: dict[str, list[bool]] = {}
    for r in rows:
        per_model_wins.setdefault(r["model"], []).append(r["correct_pairwise"])
    all_or_none = sum(1 for v in per_model_wins.values() if all(v) or not any(v))

    failures = sorted(rows, key=lambda r: r["margin_top1"])[:12]

    return {
        "probe": "visual-identity-clip",
        "status": "ok",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "model": {
            "name": model_name,
            "backend": "UForm3 ONNX (CPU) via src/equiplens/gate.py",
            "image_embed_dim": 256,
            "text_template": LABEL_TEMPLATE,
            "truck_label": TRUCK_LABEL,
        },
        "method": {
            "image_embedding": "UForm3 image encoder，单位向量，余弦相似度",
            "candidates": ["true: a photo of a {asset_meta.model}",
                           "random: a photo of a {另一随机 model}",
                           "truck: a photo of a truck"],
            "random_control": "从完整语料的 model 标签集合里按 asset_id 种子随机抽取，排除同标签",
            "same_category_control": "从同 run（类目代理）的 model 标签里按种子抽取",
            "metrics": "3 选 1 top-1 准确率；true-vs-random 二选一准确率；top1 margin = sim_true - max(其余)；Wilson 95% CI",
            "prior_control": "留一文本先验 = 该标签对其余图的平均余弦；corrected = sim - prior",
            "limitations": ["asset_meta.model 是检索查询目标，非人工核对真值（标签噪声）",
                            "UForm3 是英文模型，中文型号标签主要靠品牌/型号字母片段",
                            "图片多为 503–1200px 网络图，含部件特写/多车背景"],
        },
        "corpus": {
            "source": "data-test/runs/m43-*/state.json (asset_meta)",
            "n_assets": n,
            "n_models": n_models,
            "n_runs": n_runs,
            "label_source": "state.json asset_meta[*].model (检索查询目标标签，含噪声)",
            "label_script_counts": {
                "cjk": sum(1 for r in rows if r["label_script"] == "cjk"),
                "latin_only": sum(1 for r in rows if r["label_script"] == "latin_only"),
            },
            "dedupe": "按 asset_id；base 批次优先于 sess 批次",
            "n_text_labels": n_text_labels,
            "read_errors": read_errors,
        },
        "metrics": {
            "n": n,
            "mean_sims": {k: (round(sum(r["sims"][k] for r in rows) / n, 4) if n else None)
                          for k in ("true", "random", "truck")},
            "accuracy_3way": round(correct / n, 4),
            "accuracy_3way_wilson95": _wilson(correct, n),
            "accuracy_pairwise_true_vs_random": round(pairwise / n, 4),
            "accuracy_pairwise_wilson95": _wilson(pairwise, n),
            "pairwise_true_vs_same_category_random": {
                "n": len(same_rows),
                "accuracy": round(same_correct / len(same_rows), 4) if same_rows else None,
            },
            "pairwise_split_by_random_label_category": {
                "cross_category": {
                    "n": len(cross_cat_rows),
                    "accuracy": (round(sum(1 for r in cross_cat_rows if r["correct_pairwise"])
                                       / len(cross_cat_rows), 4) if cross_cat_rows else None),
                },
                "same_category": {
                    "n": len(same_cat_rows),
                    "accuracy": (round(sum(1 for r in same_cat_rows if r["correct_pairwise"])
                                       / len(same_cat_rows), 4) if same_cat_rows else None),
                },
            },
            "top1_breakdown": {
                "true": correct,
                "random": sum(1 for r in rows if r["top1"] == "random"),
                "truck": truck_wins,
            },
            "truck_top1_rate": round(truck_wins / n, 4),
            "margin_top1": _percentiles([r["margin_top1"] for r in rows]),
            "margin_pairwise": _percentiles([r["margin_pairwise"] for r in rows]),
            "margin_pairwise_same_category": _percentiles(
                [r["margin_pairwise_same_category"] for r in same_rows]
            ) if same_rows else {},
            "text_prior_control": {
                "description": ("每条资产用‘该文本标签对其余图的平均余弦’作留一先验；"
                                "corrected = sim - prior。若 corrected 仍≈50%，说明原始胜负"
                                "来自标签文本偏置而非图像身份证据。"),
                "accuracy_3way_prior_corrected": round(prior_correct / n, 4),
                "accuracy_pairwise_prior_corrected": round(prior_pairwise / n, 4),
                "accuracy_pairwise_wilson95": _wilson(prior_pairwise, n),
                "margin_pairwise_prior_corrected": _percentiles(
                    [r["margin_pairwise_prior_corrected"] for r in rows]
                ),
                "top1_breakdown": {
                    "true": prior_correct,
                    "random": sum(1 for r in rows if r["top1_prior_corrected"] == "random"),
                    "truck": sum(1 for r in rows if r["top1_prior_corrected"] == "truck"),
                },
            },
            "label_level_consistency": {
                "n_models": len(per_model_wins),
                "models_all_correct_or_all_wrong": all_or_none,
                "note": "全对/全错的型号占比高 → 胜负更像标签文本偏置，不是逐图证据",
            },
            "by_scene": group("scene"),
            "by_label_script": group("label_script"),
            "by_query_tier": group("query_tier"),
            "by_acceptance": {
                "accepted_any": block([r for r in rows if r["accepted_any"]]),
                "not_accepted": block([r for r in rows if not r["accepted_any"]]),
                "accepted_model": block([r for r in rows if r["accepted_model"]]),
            },
            "one_per_model": block(one_per_model_rows),
            "elapsed_s": elapsed,
        },
        "failure_cases": [
            {
                "asset_id": r["asset_id"],
                "run": r["run"],
                "scene": r["scene"],
                "model": r["model"],
                "random_model": r["random_model"],
                "top1": r["top1"],
                "sims": r["sims"],
                "text_prior_loo": r["text_prior_loo"],
                "margin_top1": r["margin_top1"],
                "image": r["image"],
            }
            for r in failures
        ],
        "rows": rows,
    }


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="S2-01 视觉身份离线探针")
    ap.add_argument("--out", default=DEFAULT_OUT, help="输出 JSON 路径")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 个资产（试跑用）")
    args = ap.parse_args(argv)

    rows, runs_used, problems = collect_assets()
    print(f"找到 {len(rows)} 个 image+model 资产，覆盖 {len(runs_used)} 个 run、"
          f"{len({r['model'] for r in rows})} 个型号标签")
    if problems:
        print("警告:", *problems, sep="\n  ")
    if len(rows) < MIN_PAIRS:
        payload = {"probe": "visual-identity-clip", "status": "insufficient_data",
                   "n_assets": len(rows), "min_required": MIN_PAIRS,
                   "problems": problems, "rows": []}
        out = ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"数据不足（{len(rows)} < {MIN_PAIRS}），写 {args.out} 后退出。")
        return 2

    from equiplens import gate
    t0 = time.time()
    results, run_info = run_probe(rows, limit=args.limit)
    print(f"打分完成：{len(results)} 条，{run_info['elapsed_s']}s，"
          f"读图失败 {len(run_info['read_errors'])}")
    if not results:
        print("没有可打分的资产（检查 --limit 与图片/标签），未写输出。", file=sys.stderr)
        return 1
    summary = summarize(results, n_models=len({r["model"] for r in results}),
                        n_runs=len({r["run"] for r in results}),
                        elapsed=run_info["elapsed_s"], read_errors=run_info["read_errors"],
                        model_name=gate.MODEL_NAME,
                        n_text_labels=run_info.get("n_text_labels", 0))
    if problems:
        summary["corpus"]["problems"] = problems

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(out)

    m = summary["metrics"]
    print(f"N={m['n']}  models={summary['corpus']['n_models']}  "
          f"3way_acc={m['accuracy_3way']:.3f}  pairwise={m['accuracy_pairwise_true_vs_random']:.3f}  "
          f"truck_top1={m['truck_top1_rate']:.3f}")
    print(f"margin_top1 median={m['margin_top1'].get('median')}  "
          f"p10={m['margin_top1'].get('p10')}  p90={m['margin_top1'].get('p90')}")
    print(f"-> {args.out}  (total {time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
