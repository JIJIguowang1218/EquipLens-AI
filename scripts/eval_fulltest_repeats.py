# -*- coding: utf-8 -*-
"""汇总 P3 重复测试：每类目多次的均值/极差/CV，已知 vs holdout，稳定性判定。

用法: PYTHONPATH=src python scripts/eval_fulltest_repeats.py \
        --roots data-test/runs/p7-screen-20261114,data-test/runs/p7-screen-r2-20261114,data-test/runs/p7-screen-r3-20261114
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from eval_fulltest import load_case  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", required=True)
    args = ap.parse_args()
    roots = [ROOT / r.strip() for r in args.roots.split(",") if r.strip()]
    cases = json.loads((ROOT / "data-test/evals/fulltest-20261114/CASES.json")
                       .read_text(encoding="utf-8"))
    groups = {c["name"]: c.get("group", "known") for c in cases}
    per_case: dict[str, list[dict]] = {c["name"]: [] for c in cases}
    for root in roots:
        for name in per_case:
            d = root / name
            if d.exists():
                per_case[name].append(load_case(d))
    summary = {}
    for name, runs in per_case.items():
        ok = [r for r in runs if "error" not in r]
        if not ok:
            continue
        dr = [r["delivered"] / r["required"] for r in ok if r["required"]]
        bk = [r["backup"] for r in ok]
        dg = [r["degraded_ratio"] or 0 for r in ok]
        summary[name] = {
            "group": groups.get(name),
            "runs": len(ok),
            "delivery_rate_mean": round(statistics.mean(dr), 3),
            "delivery_range": round(max(dr) - min(dr), 3),
            "backup_mean": round(statistics.mean(bk), 2),
            "backup_range": max(bk) - min(bk),
            "degraded_mean": round(statistics.mean(dg), 3),
            "degraded_cv": round(statistics.pstdev(dg) / statistics.mean(dg), 3)
            if statistics.mean(dg) else 0.0,
            "no_hits_mean": round(statistics.mean([r["no_hits"] for r in ok]), 2),
            "cost_mean": round(statistics.mean([r["cost_peak"] or 0 for r in ok]), 3),
            "elapsed_mean_s": round(statistics.mean([r["elapsed_s"] for r in ok]), 1),
            "pool_ok_share": round(statistics.mean([1.0 if r["pool_ok"] else 0.0
                                                    for r in ok]), 2),
        }
    def agg(group: str) -> dict:
        rows = [v for v in summary.values() if v["group"] == group]
        return {
            "cases": len(rows),
            "delivery_rate_mean": round(statistics.mean(
                [r["delivery_rate_mean"] for r in rows]), 3),
            "backup_mean": round(statistics.mean([r["backup_mean"] for r in rows]), 2),
            "degraded_mean": round(statistics.mean([r["degraded_mean"] for r in rows]), 3),
            "no_hits_mean": round(statistics.mean([r["no_hits_mean"] for r in rows]), 2),
        }
    known, hold = agg("known"), agg("holdout")
    stability = {
        "max_delivery_range": max(v["delivery_range"] for v in summary.values()),
        "max_backup_range": max(v["backup_range"] for v in summary.values()),
        "max_degraded_cv": max(v["degraded_cv"] for v in summary.values()),
        "all_cases_3_runs": all(v["runs"] >= 3 for v in summary.values()),
    }
    verdict = {
        "delivery_hold_vs_known": round(hold["delivery_rate_mean"]
                                        / known["delivery_rate_mean"], 3)
        if known["delivery_rate_mean"] else None,
        "go_stability": bool(stability["max_delivery_range"] <= 1 / 6
                             and stability["max_backup_range"] <= 1
                             and stability["max_degraded_cv"] <= 0.25
                             and stability["all_cases_3_runs"]),
    }
    out = {"roots": [str(r.relative_to(ROOT)) for r in roots],
           "cases": summary, "known": known, "holdout": hold,
           "stability": stability, "verdict": verdict}
    dest = ROOT / "data-test/evals" / "fulltest-repeats.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"known": known, "holdout": hold,
                      "stability": stability, "verdict": verdict},
                     ensure_ascii=False, indent=1))
    for k, v in summary.items():
        print(f"{k:20s} runs={v['runs']} deliv={v['delivery_rate_mean']} "
              f"range={v['delivery_range']} bk={v['backup_mean']}(±{v['backup_range']}) "
              f"deg={v['degraded_mean']} cv={v['degraded_cv']} nohit={v['no_hits_mean']}")
    print("out:", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
