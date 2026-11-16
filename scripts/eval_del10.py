# -*- coding: utf-8 -*-
"""Summarise the 10-case delivery regression (5 existing + 5 new classes)."""
from __future__ import annotations

import json
from pathlib import Path

CASES = ["c1e", "h2e", "h3e", "c4e", "c5e", "s1", "s2", "s3", "s4", "s5"]
PLAN_DIRS = {"c1e": "m43e", "h2e": "m43e", "h3e": "m43e", "c4e": "m43e", "c5e": "m43e",
             "s1": "m43f", "s2": "m43f", "s3": "m43f", "s4": "m43f", "s5": "m43f"}


def load(path: Path) -> dict:
    try:
        raw = path.read_bytes()
    except Exception as exc:  # noqa: BLE001
        return {"_error": str(exc)}
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            return json.loads(raw.decode(enc))
        except Exception:  # noqa: BLE001
            continue
    return {"_error": "decode"}


def main() -> int:
    rows = []
    for case in CASES:
        d = load(Path("data-test/evals") / f"del10-{case}.json")
        de = d.get("delivery") or {}
        plan = load(Path("data-test/plans") / PLAN_DIRS[case] / f"{case}.json")
        pool = plan.get("pool") or {}
        rows.append({
            "case": case,
            "state": d.get("state"),
            "delivered": de.get("delivered"),
            "required": de.get("required"),
            "missing": de.get("missing"),
            "degraded": de.get("degraded"),
            "backup": (de.get("backup") or {}).get("delivered"),
            "backup_required": (de.get("backup") or {}).get("required"),
            "queries": (d.get("budget_used") or {}).get("queries"),
            "seconds": round((d.get("elapsed_ms") or 0) / 1000, 1),
            "plan_candidates": pool.get("count"),
            "pool_required": pool.get("required"),
            "pool_ok": pool.get("ok"),
            "error": d.get("_error"),
        })
    out = {"cases": rows}
    Path("data-test/evals/del10-summary-20261116.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print("| case | delivered | missing | degraded | backup | queries | s | pool |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['case']} | {r['delivered']}/{r['required']} | {r['missing']} | "
              f"{r['degraded']} | {r['backup']}/{r['backup_required']} | {r['queries']} | "
              f"{r['seconds']} | {r['plan_candidates']}/{r['pool_required']} |")
    total_req = sum((r["required"] or 0) for r in rows)
    total_del = sum((r["delivered"] or 0) for r in rows)
    missing = sum((r["missing"] or 0) for r in rows)
    print(f"\ntotal delivered {total_del}/{total_req}, missing {missing}, "
          f"cases with missing: {[r['case'] for r in rows if r['missing']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
