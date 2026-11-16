# -*- coding: utf-8 -*-
"""Evaluate the LLM router on the 100-turn blind holdout."""
from __future__ import annotations

import json
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
            Path("data-test/evals/router-holdout100-20261116.jsonl").read_text(
                encoding="utf-8").splitlines() if l.strip()]
    key = load_key()
    results = []
    for r in rows:
        try:
            got = classify(r["text"], context=None, api_key=key, rules_fallback=False)
        except Exception as e:  # noqa: BLE001
            results.append({**r, "got": [], "error": f"{type(e).__name__}: {e}"})
            continue
        results.append({**r, "got": got.get("targets") or [],
                        "hard": bool(got.get("hard")), "clarify": bool(got.get("clarify"))})

    def ok(r):
        exp, got = set(r["expect_targets"]), set(r["got"])
        return (got == set()) if not exp else exp <= got

    exact = sum(1 for r in results if ok(r)) / max(1, len(results))
    any_hit = sum(1 for r in results
                  if set(r["expect_targets"]) & set(r["got"])) / max(1, len(results))
    hard_ok = sum(1 for r in results if r.get("hard") == r.get("expect_hard")) / max(1, len(results))
    fails = [r for r in results if not ok(r)]

    out = {"n": len(results), "exact_subset": round(exact, 3),
           "any_overlap": round(any_hit, 3), "hard_match": round(hard_ok, 3),
           "errors": sum(1 for r in results if r.get("error")),
           "rows": results, "failures": fails}
    Path("data-test/evals/router-holdout100-20261116-result.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"n={out['n']} exact_subset={out['exact_subset']} any_overlap={out['any_overlap']} "
          f"hard_match={out['hard_match']} errors={out['errors']}")
    for r in fails[:15]:
        print(f"  FAIL {r['id']}: {r['text'][:40]} | want {r['expect_targets']} got {r['got']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
