# -*- coding: utf-8 -*-
"""Score the current router run against the user-reviewed (relabeled) holdout."""
from __future__ import annotations
import json
from pathlib import Path

def ok(row, got, feas):
    exp = row["expect_targets"]
    if not exp:
        want_f = row.get("expect_feasibility")
        if want_f:
            return (not got) and feas == want_f
        return not got
    got_s = set(got)
    alt = row.get("accept_alt") or {}
    return all((t in got_s) or any(a in got_s for a in alt.get(t, [])) for t in exp)

def main():
    labels = [json.loads(l) for l in Path("data-test/evals/router-holdout100-20261116-relabeled.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    res = {r["id"]: r for r in json.load(open("data-test/evals/router-holdout100-20261116-result.json", encoding="utf-8"))["rows"]}
    rows = []
    for r in labels:
        g = res.get(r["id"], {})
        got = g.get("got") or []
        feas = g.get("feasibility")
        rows.append({**r, "got": got, "feasibility": feas, "ok": ok(r, got, feas)})
    all_ok = sum(1 for r in rows if r["ok"])
    real = [r for r in rows if r["realistic"]]
    real_ok = sum(1 for r in real if r["ok"])
    cap_rows = [r for r in rows if r.get("expect_feasibility")]
    cap_ok = sum(1 for r in cap_rows if r["ok"])
    fails = [r for r in rows if not r["ok"]]
    out = {"all": [all_ok, len(rows)], "realistic": [real_ok, len(real)],
           "capability": [cap_ok, len(cap_rows)], "failures": fails, "rows": rows}
    Path("data-test/evals/router-holdout100-20261116-relabeled-result.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"all {all_ok}/{len(rows)}; realistic {real_ok}/{len(real)}; capability {cap_ok}/{len(cap_rows)}")
    for r in fails:
        print("FAIL", r["id"], r["text"], "want", r["expect_targets"], "got", r["got"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
