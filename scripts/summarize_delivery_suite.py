# -*- coding: utf-8 -*-
"""汇总 delivery-20261112 套件：跨 5 个输入对比交付/成本/耗时。

用法:
  PYTHONPATH=src python scripts/summarize_delivery_suite.py \
      --base data-test/runs/delivery-20261112
输出: <base>/SUMMARY.md + <base>/SUMMARY.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def collect(case: Path) -> dict:
    run = case / "run"
    d = _read(run / "DELIVERY.json") or {}
    st = _read(run / "state.json") or {}
    plan = _read(case / "plan-ranked.json") or _read(case / "plan.json") or {}
    brief = _read(case / "brief.json") or {}
    assets = st.get("assets") or {}
    with_img = sum(1 for t, p in assets.items()
                   if any((v or []) for v in (p or {}).values()))
    mon = d.get("monitoring") or {}
    dl = d.get("user_delivery") or {}
    sm = dl.get("summary") or {}
    pool = plan.get("pool") or {}
    timings: dict[str, int] = {}
    for t in (mon.get("timings") or []):
        k = t.get("state") or "?"
        timings[k] = timings.get(k, 0) + int(t.get("ms") or 0)
    return {
        "case": case.name,
        "class": (brief.get("request") or {}).get("class") or "",
        "slots": (brief.get("request") or {}).get("page_budget", {}).get("vehicle_slots"),
        "backup_req": (brief.get("request") or {}).get("page_budget", {}).get("backup_slots", 4),
        "plan_candidates": len(plan.get("candidates") or []),
        "pool_need": pool.get("required"),
        "pool_ok": pool.get("ok"),
        "targets": len(st.get("targets") or {}),
        "with_images": with_img,
        "delivered": sm.get("delivered"),
        "required": sm.get("required"),
        "backup": len(dl.get("backup") or []),
        "degraded": sm.get("degraded"),
        "citation_only": sm.get("citation_only"),
        "fetches": (sm.get("budget") or (st.get("budget_used") or {})).get("fetches")
        if isinstance(sm.get("budget"), dict) else (st.get("budget_used") or {}).get("fetches"),
        "downloads": mon.get("downloads") or {},
        "elapsed_s": round((mon.get("elapsed_ms") or 0) / 1000, 1),
        "timings_ms": timings,
        "cost_peak": (mon.get("cost_cny") or {}).get("peak", {}).get("total"),
        "cost_off": (mon.get("cost_cny") or {}).get("off_peak", {}).get("total"),
        "usage": mon.get("usage") or {},
        "unavailable": mon.get("unavailable") or [],
    }


def render(rows: list[dict]) -> str:
    lines = [
        "# 交付测试汇总（5 个输入）",
        "",
        "> 每个 case 独立目录；brief/plan/rank/loop 全部走 API 与规则代码，无手工字段。",
        "",
        "## 1. 交付结果",
        "",
        "| 输入 | 类目 | 槽位 | 候选 | 需池 | 发现 | 有图 | 交付 | 备选 | degraded | citation | 池告警 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        ok = "—" if r["pool_ok"] in (None, True) else "**WARN**"
        lines.append(
            f"| {r['case']} | {r['class']} | {r['slots']} | {r['plan_candidates']} | "
            f"{r['pool_need']} | {r['targets']} | {r['with_images']} | "
            f"{r['delivered']}/{r['required']} | {r['backup']}/{r['backup_req']} | "
            f"{r['degraded']} | {r['citation_only']} | {ok} |")
    lines += ["", "## 2. 成本（同一份用量，峰/谷两口径，单位 ¥）", "",
              "| 输入 | chat tokens in/out | Search/Fetch | 全高峰 | 全空闲 |",
              "|---|---|---:|---:|---:|"]
    for r in rows:
        u = r["usage"]
        lines.append(f"| {r['case']} | {u.get('tokens_in_miss', 0)} / {u.get('tokens_out', 0)} | "
                     f"{u.get('search_calls', 0)} / {u.get('fetch_calls', 0)} | "
                     f"¥{r['cost_peak']} | ¥{r['cost_off']} |")
    lines += ["", "## 3. 耗时（秒；节点明细见各 case 的 DELIVERY.md）", "",
              "| 输入 | 总耗时 | 主要节点 (state=ms) |",
              "|---|---:|---|"]
    for r in rows:
        top = sorted((r["timings_ms"] or {}).items(), key=lambda kv: -kv[1])[:4]
        lines.append(f"| {r['case']} | {r['elapsed_s']} | "
                     + " · ".join(f"{k}={v}" for k, v in top) + " |")
    lines += ["", "## 4. 缺图归因", ""]
    for r in rows:
        counts: dict[str, int] = {}
        for x in r["unavailable"]:
            k = x.get("reason") or "unknown"
            counts[k] = counts.get(k, 0) + 1
        lines.append(f"- {r['case']}: " + (" / ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "—"))
    lines += ["", "## 5. 下载质量", "",
              "| 输入 | hits | downloaded | failed | blocked | gate_pass |",
              "|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        d = r["downloads"]
        lines.append(f"| {r['case']} | {d.get('hits')} | {d.get('downloaded')} | "
                     f"{d.get('failed')} | {d.get('blocked')} | {d.get('gate_pass')} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(ROOT / "data-test" / "runs" / "delivery-20261112"))
    args = ap.parse_args(argv)
    base = Path(args.base)
    cases = sorted([d for d in base.iterdir() if (d / "brief.json").exists()])
    rows = [collect(c) for c in cases]
    (base / "SUMMARY.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    (base / "SUMMARY.md").write_text(render(rows), encoding="utf-8")
    print(f"cases={len(rows)} -> {base/'SUMMARY.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
