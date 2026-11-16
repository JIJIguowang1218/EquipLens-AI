# -*- coding: utf-8 -*-
"""Summarise the pool-supply pre-registration runs (8 briefs x 3 arms)."""
from __future__ import annotations

import json
from pathlib import Path

BRIEFS = ["c1-desert", "h2-wrecker", "h3-sweeper", "c4-forklift", "c5-roller",
          "v-brand", "v-foreign", "v-longtail"]
ARMS = ["default", "topup4", "wide"]


def load(path: Path) -> dict:
    raw = path.read_bytes()
    for enc in ("utf-8", "gbk"):
        try:
            return json.loads(raw.decode(enc))
        except Exception:  # noqa: BLE001
            continue
    return {}


def main() -> int:
    rows = []
    for b in BRIEFS:
        row = {"brief": b}
        for arm in ARMS:
            d = load(Path("data-test/plans/pool") / f"{b}__{arm}.json")
            pool = d.get("pool") or {}
            row[arm] = {
                "candidates": pool.get("count"),
                "required": pool.get("required"),
                "ok": pool.get("ok"),
                "verifiable_share": pool.get("verifiable_share"),
                "queries": len(d.get("queries") or []),
            }
        rows.append(row)

    summary = {}
    for arm in ARMS:
        ok = sum(1 for r in rows if r[arm]["ok"])
        cand = [r[arm]["candidates"] or 0 for r in rows]
        share = [r[arm]["verifiable_share"] or 0 for r in rows]
        summary[arm] = {
            "pool_ok": ok, "pool_ok_rate": round(ok / len(rows), 3),
            "candidates_mean": round(sum(cand) / len(cand), 1),
            "verifiable_share_mean": round(sum(share) / len(share), 3),
            "queries_mean": round(sum((r[arm]["queries"] or 0) for r in rows) / len(rows), 1),
        }

    out = {"briefs": rows, "summary": summary}
    Path("data-test/evals/pool-supply-20261116.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print("| brief | default | topup4 | wide |")
    print("|---|---|---|---|")
    for r in rows:
        cells = []
        for arm in ARMS:
            a = r[arm]
            cells.append(f"{a['candidates']}/{a['required']} {'ok' if a['ok'] else 'SHORT'}")
        print(f"| {r['brief']} | " + " | ".join(cells) + " |")
    print()
    for arm in ARMS:
        s = summary[arm]
        print(f"{arm}: pool_ok {s['pool_ok']}/8, candidates avg {s['candidates_mean']}, "
              f"verifiable {s['verifiable_share_mean']:.1%}, queries avg {s['queries_mean']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
