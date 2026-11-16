# -*- coding: utf-8 -*-
"""Run the 290 staged P3 inputs through the current LLM router and score them."""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

KEY_FILE = Path.home() / ".equiplens" / "deepseek.env"


def load_key() -> str:
    import os
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("DEEPSEEK_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no key")


def main() -> int:
    from equiplens.session_router import classify

    rows = [json.loads(l) for l in
            Path("data-test/evals/p3-staged-290-20261117.jsonl").read_text(
                encoding="utf-8").splitlines() if l.strip()]
    key = load_key()

    def run(r):
        try:
            got = classify(r["text"], context={"stage": r["stage"]}, api_key=key)
        except Exception as e:  # noqa: BLE001
            return {**r, "got": [], "action": "error", "feasibility": None,
                    "message": f"{type(e).__name__}: {e}"}
        return {**r, "got": got.get("targets") or [],
                "action": got.get("action") or "apply",
                "feasibility": got.get("feasibility"),
                "message": got.get("message") or ""}

    with ThreadPoolExecutor(max_workers=4) as pool:
        res = list(pool.map(run, rows))

    def ok(r):
        exp_action = r.get("expect_action") or "apply"
        if exp_action in ("guide", "explain"):
            if r["got"] or r["action"] != exp_action:
                return False
            want_f = r.get("expect_feasibility")
            return (not want_f) or r.get("feasibility") == want_f
        return set(r.get("expect_targets") or []) <= set(r["got"])

    for r in res:
        r["ok"] = ok(r)

    def rate(items):
        return (sum(1 for r in items if r["ok"]), len(items))

    stages = {}
    for s in ("pre_run", "running", "delivered"):
        stages[s] = rate([r for r in res if r["stage"] == s])
    cats = {}
    for c in sorted({r["category"] for r in res}):
        cats[c] = rate([r for r in res if r["category"] == c])
    fails = [r for r in res if not r["ok"]]
    out = {"all": rate(res), "stages": stages, "categories": cats,
           "failures": fails, "rows": res}
    Path("data-test/evals/p3-staged-290-result-20261117.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"all {out['all'][0]}/{out['all'][1]}")
    for s, (a, b) in stages.items():
        print(f"  {s}: {a}/{b}")
    for c, (a, b) in cats.items():
        print(f"  {c}: {a}/{b}")
    print("failures:")
    for r in fails[:40]:
        print(f"  {r['id']} [{r['category']}] {r['text']} | want {r['expect_targets']} "
              f"{r.get('expect_action')} {r.get('expect_feasibility') or ''} | got {r['got']} "
              f"{r['action']} {r.get('feasibility') or ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
