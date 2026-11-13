# -*- coding: utf-8 -*-
"""A1 离线评估：按“来源维度”降权离类候选（不查类目词表、不联网）。

规则（提案）：候选必须至少一条来源来自 base 或 model 维度；
只有 environment/unit/english/topup 来源的候选降到 pool 尾部（不删）。
本脚本只统计影响面，不改任何数据。
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

ANCHOR = {"base", "model"}


def main() -> int:
    rows = []
    totals = Counter()
    for p in sorted((ROOT / "data-test" / "runs").rglob("plan.json")):
        try:
            j = json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        cands = j.get("candidates") or []
        if not cands:
            continue
        req = (j.get("pool") or {}).get("required") or 0
        keep, demote = [], []
        for c in cands:
            dims = set(c.get("dimensions") or [])
            (keep if dims & ANCHOR else demote).append(c)
        totals["plans"] += 1
        totals["candidates"] += len(cands)
        totals["demoted"] += len(demote)
        if req and len(keep) < req:
            totals["plans_below_required"] += 1
        rows.append({
            "plan": str(p.parent.relative_to(ROOT)),
            "candidates": len(cands),
            "keep": len(keep),
            "demoted": len(demote),
            "required": req,
            "keep_below_required": bool(req and len(keep) < req),
            "demoted_samples": [c.get("model") for c in demote[:6]],
        })
    # 重点：11-13 wide 套件（c2 混入牵引车的那批）
    focus = [r for r in rows if "p1-wide" in r["plan"] or "delivery-20261113" in r["plan"]]
    out = {"totals": dict(totals), "focus": focus}
    dest = ROOT / "data-test" / "evals" / "source-provenance-20261114.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(totals), ensure_ascii=False, indent=1))
    for r in focus[:8]:
        print(f"{r['plan'][-46:]:48s} cand={r['candidates']:2d} keep={r['keep']:2d} "
              f"demote={r['demoted']:2d} req={r['required']} below={r['keep_below_required']}")
        if r["demoted_samples"]:
            print("    demoted:", [m[:22] for m in r["demoted_samples"]])
    print("out:", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
