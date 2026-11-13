# -*- coding: utf-8 -*-
"""评估 10 类目筛查：指标、分组对比、Go/No-Go 判定。

用法: PYTHONPATH=src python scripts/eval_fulltest.py --root data-test/runs/p7-screen-20261114
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_case(case_dir: Path) -> dict:
    sm = case_dir / "run" / "summary.json"
    if not sm.exists():
        return {"error": "no summary"}
    s = json.loads(sm.read_text(encoding="utf-8"))
    d = s.get("delivery") or {}
    dl = case_dir / "run" / "DELIVERY.json"
    cost = None
    if dl.exists():
        try:
            cost = json.loads(dl.read_text(encoding="utf-8"))["monitoring"]["cost_cny"]["peak"]["total"]
        except Exception:  # noqa: BLE001
            cost = None
    plan = case_dir / "plan.json"
    cands = pool_ok = None
    if plan.exists():
        try:
            p = json.loads(plan.read_text(encoding="utf-8"))
            cands = len(p.get("candidates") or [])
            pool_ok = bool((p.get("pool") or {}).get("ok"))
        except Exception:  # noqa: BLE001
            pass
    unavailable = d.get("unavailable") or []
    return {
        "state": s.get("state"),
        "required": d.get("required"),
        "delivered": d.get("delivered"),
        "backup": (d.get("backup") or {}).get("delivered"),
        "degraded": d.get("degraded"),
        "degraded_ratio": d.get("degraded_ratio"),
        "citation_only": d.get("citation_only"),
        "no_hits": sum(1 for u in unavailable if u.get("reason") == "no_hits"),
        "unavailable": len(unavailable),
        "query_tiers": d.get("query_tiers"),
        "downloads": s.get("downloads"),
        "elapsed_s": round((s.get("elapsed_ms") or 0) / 1000, 1),
        "cost_peak": cost,
        "plan_candidates": cands,
        "pool_ok": pool_ok,
        "config": s.get("config"),
    }


def agg(rows: list[dict]) -> dict:
    ok = [r for r in rows if "error" not in r]
    if not ok:
        return {}
    req = sum(r["required"] or 0 for r in ok)
    deliv = sum(r["delivered"] or 0 for r in ok)
    backup = sum(r["backup"] or 0 for r in ok)
    return {
        "cases": len(ok),
        "required": req,
        "delivered": deliv,
        "delivery_rate": round(deliv / req, 3) if req else 0,
        "backup": backup,
        "backup_rate": round(backup / (4 * len(ok)), 3) if ok else 0,
        "degraded_ratio_mean": round(statistics.mean(
            [r["degraded_ratio"] or 0 for r in ok]), 3),
        "no_hits": sum(r["no_hits"] or 0 for r in ok),
        "cost_peak_sum": round(sum(r["cost_peak"] or 0 for r in ok), 3),
        "elapsed_s_sum": round(sum(r["elapsed_s"] or 0 for r in ok), 1),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    root = ROOT / args.root
    cases = json.loads((ROOT / "data-test/evals/fulltest-20261114/CASES.json")
                       .read_text(encoding="utf-8"))
    groups = {c["name"]: c.get("group", "known") for c in cases}
    rows = {}
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        rows[d.name] = load_case(d)
    known = {k: v for k, v in rows.items() if groups.get(k) == "known"}
    holdout = {k: v for k, v in rows.items() if groups.get(k) == "holdout"}
    a_known, a_hold = agg(list(known.values())), agg(list(holdout.values()))
    verdict = {}
    if a_known and a_hold:
        verdict["delivery_ratio_hold_vs_known"] = round(
            (a_hold["delivery_rate"] / a_known["delivery_rate"]), 3) \
            if a_known["delivery_rate"] else None
        verdict["no_hits_ratio"] = round(
            (a_hold["no_hits"] / max(1, a_known["no_hits"])), 3)
        verdict["go"] = bool(
            a_hold["delivery_rate"] >= 0.8 * a_known["delivery_rate"]
            and a_hold["no_hits"] <= 1.5 * max(1, a_known["no_hits"])
            and all("error" not in v for v in rows.values()))
    out = {"root": args.root, "cases": rows, "known": a_known,
           "holdout": a_hold, "verdict": verdict}
    dest = ROOT / "data-test/evals" / f"fulltest-eval-{root.name}.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"known": a_known, "holdout": a_hold, "verdict": verdict},
                     ensure_ascii=False, indent=1))
    for k, v in rows.items():
        print(f"{k:22s} {v.get('delivered')}/{v.get('required')} bk={v.get('backup')} "
              f"deg={v.get('degraded')} nohit={v.get('no_hits')} cost={v.get('cost_peak')} "
              f"{v.get('elapsed_s')}s tiers={v.get('query_tiers')}")
    print("out:", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
