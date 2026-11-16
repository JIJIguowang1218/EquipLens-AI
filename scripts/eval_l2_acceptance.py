# -*- coding: utf-8 -*-
"""L2 5-case acceptance: intents vs the blind user script + delivery metrics."""
from __future__ import annotations

import json
from pathlib import Path

CASES = ["c1e", "h2e", "h3e", "c4e", "c5e"]
EXPECT = {
    2: {"fill.quota"},
    3: {"plan.negative"},
    4: {"delivered.replace", "verify.blacklist"},
    5: {"fetch.filters.quality"},
    6: {"delivery.report"},
}


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def main() -> int:
    rows = []
    for case in CASES:
        sess = load(Path("data-test/sessions") / f"l2e-{case}.json")
        s = sess.get("session") or {}
        run_dir = Path("data-test/runs") / f"l2e-{case}"
        summary = load(run_dir / "summary.json")
        delivery = summary.get("delivery") or {}
        events = [e for e in (s.get("events") or []) if e.get("kind") == "user_msg"]
        turns = {}
        for e in events:
            res = e.get("result") or {}
            turns[len(turns) + 2] = set(res.get("targets") or [])
        score = 0
        detail = {}
        for turn, want in EXPECT.items():
            got = turns.get(turn, set())
            ok = bool(got & want)
            score += 1 if ok else 0
            detail[turn] = {"want": sorted(want), "got": sorted(got), "ok": ok}
        deliv = s.get("delivered") or []
        keys = [f"{d.get('url')}|{d.get('sha1')}|{d.get('model')}|{d.get('target')}" for d in deliv]
        row = {
            "case": case,
            "delivered": delivery.get("delivered"),
            "required": delivery.get("required"),
            "missing": delivery.get("missing"),
            "degraded": delivery.get("degraded"),
            "intent_score": f"{score}/5",
            "intents": detail,
            "patches": [p.get("target") for p in s.get("patches") or []],
            "session_patches": (summary.get("config") or {}).get("session_patches"),
            "duplicate_deliveries": len(keys) - len(set(keys)),
            "delivery_format": (s.get("preferences") or {}).get("delivery", {}).get("format"),
            "session_state": s.get("state"),
        }
        rows.append(row)

    out = {"cases": rows}
    Path("data-test/evals/l2-acceptance-20261116.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print("| case | delivered | missing | degraded | intents | patches | dup | state |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['case']} | {r['delivered']}/{r['required']} | {r['missing']} | "
              f"{r['degraded']} | {r['intent_score']} | {len(r['patches'])} | "
              f"{r['duplicate_deliveries']} | {r['session_state']} |")
    total = sum(int(r["intent_score"].split("/")[0]) for r in rows)
    print(f"\nintent total: {total}/{5 * len(rows)}")
    ok = all(r["missing"] == 0 and r["duplicate_deliveries"] == 0 for r in rows)
    print("delivery gate:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
