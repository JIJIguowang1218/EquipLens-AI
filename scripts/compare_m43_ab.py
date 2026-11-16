# -*- coding: utf-8 -*-
"""Compare the M4.3 A/B arms: baseline (plain run) vs session (delta patch at FETCH)."""
from __future__ import annotations

import json
from pathlib import Path

CASES = ["c1-desert", "h2-wrecker", "h3-sweeper", "c4-forklift", "c5-roller"]
EVAL = Path("data-test/evals")


def load(path: Path) -> dict:
    """Baseline JSON is written by the engine CLI on Windows (GBK stdout)."""
    try:
        raw = path.read_bytes()
    except Exception as exc:  # noqa: BLE001
        return {"_error": f"{type(exc).__name__}: {exc}"}
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            return json.loads(raw.decode(enc))
        except Exception:  # noqa: BLE001
            continue
    return {"_error": "cannot decode" }


def num(v, default=0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def main() -> int:
    rows = []
    for case in CASES:
        base = load(EVAL / f"m43-base-{case}.json")
        sess = load(EVAL / f"m43-sess-{case}.json")
        bd = base.get("delivery") or {}
        bq = int(num((base.get("budget_used") or {}).get("queries")))
        bsec = num(base.get("elapsed_ms")) / 1000
        sd = sess.get("delivery") or {
            "delivered": sess.get("delivered"), "required": sess.get("required"),
            "missing": sess.get("missing"), "degraded": sess.get("degraded"),
            "status": sess.get("status"),
            "backup": {"delivered": sess.get("backup_delivered"),
                       "required": sess.get("backup_required")},
        }
        sq = int(num(sess.get("queries_total")))
        dq = int(num(sess.get("delta_queries")))
        ssec = num(sess.get("elapsed_ms")) / 1000
        row = {
            "case": case,
            "base_delivered": bd.get("delivered"), "base_required": bd.get("required"),
            "base_missing": bd.get("missing"), "base_degraded": bd.get("degraded"),
            "base_backup": (bd.get("backup") or {}).get("delivered"),
            "base_queries": bq, "base_seconds": round(bsec, 1),
            "sess_delivered": sd.get("delivered"), "sess_missing": sd.get("missing"),
            "sess_degraded": sd.get("degraded"),
            "sess_backup": sd.get("backup_delivered"),
            "sess_queries": sq, "delta_queries": dq,
            "delta_ratio_of_base": round(dq / bq, 3) if bq else None,
            "delta_queries_round": sess.get("delta_queries_round"),
            "delta_round_ratio": (round(int(sess.get("delta_queries_round")) / bq, 3)
                                  if sess.get("delta_queries_round") is not None and bq else None),
            "sess_seconds": round(ssec, 1),
            "time_increase": round((ssec - bsec) / bsec, 3) if bsec else None,
            "duplicate_targets": sess.get("duplicate_targets"),
            "patched_model": (sess.get("patch") or {}).get("added_model"),
            "base_error": base.get("_error"), "sess_error": sess.get("_error"),
        }
        rows.append(row)

    metrics = []
    for r in rows:
        metrics.append({
            "case": r["case"],
            "exact_complete": (r["base_missing"] == 0 and r["sess_missing"] == 0),
            "no_duplicate": (r["duplicate_targets"] in (0, None)),
            "delta_query_le_25": (r["delta_round_ratio"] is not None
                                  and r["delta_round_ratio"] <= 0.25),
            "time_increase_le_20": (r["time_increase"] is not None
                                    and r["time_increase"] <= 0.20),
            "delivered_delta": (num(r["sess_delivered"]) - num(r["base_delivered"])),
        })

    out = {"cases": rows, "metrics": metrics}
    (EVAL / "m43-ab-compare.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                              encoding="utf-8")

    print("| case | base 交付 | sess 交付 | degraded | Δ查询(轮) | Δ占比 | base秒 | sess秒 | 耗时增幅 | 重复 |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['case']} | {r['base_delivered']}/{r['base_required']} | "
              f"{r['sess_delivered']}/{r['base_required']} | "
              f"{r['base_degraded']}->{r['sess_degraded']} | {r['delta_queries_round']} | "
              f"{r['delta_round_ratio']} | {r['base_seconds']} | {r['sess_seconds']} | "
              f"{r['time_increase']} | {r['duplicate_targets']} |")
    print()
    for m in metrics:
        print(f"{m['case']}: exact={m['exact_complete']} dup0={m['no_duplicate']} "
              f"delta<=25%={m['delta_query_le_25']} time<=20%={m['time_increase_le_20']} "
              f"delivered_delta={m['delivered_delta']}")
    ok = all(m["exact_complete"] and m["no_duplicate"] and m["delta_query_le_25"]
             and m["time_increase_le_20"] for m in metrics)
    print(f"\nM4.3 gate: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
