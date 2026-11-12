# -*- coding: utf-8 -*-
"""交付清单 / 内容监控：把一次 run 拆成三块。

1. **用户交付物**：N 台主交付车型的图（按部件分组）+ 任务单摘要；
2. **内部监控**：每台的实现状态（交付/备选/缺图原因）、degraded/citation_only、
   下载质量、loop 节点耗时、API 成本（峰/谷两个口径）；
3. **可复用中间产物**：任务单 JSON、plan（优先级先验）、部件图（分析/知识库候选）、
   evidence.db、audit.html。

很多产物不是直接给用户的——清单里显式分区，避免把内部监控当成交付物。

用法:
  PYTHONPATH=src python scripts/build_delivery_manifest.py \
    --run data-test/runs/<run-id> \
    --brief data-test/evals/task-briefs-20261109/brief-m1-desert.json \
    --plan data-test/runs/plan-ab4-20261111/A2/plan-ranked.json
输出: <run>/DELIVERY.json + <run>/DELIVERY.md
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

from equiplens import pricing  # noqa: E402


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except OSError:
        pass
    return rows


def collect_usage(run_dir: Path, plan_path: Path | None = None) -> dict:
    """chat tokens + search/fetch 成功调用数（用于峰谷计价）。"""
    rows = _read_jsonl(run_dir / "api_log.jsonl")
    if plan_path:
        rows += _read_jsonl(Path(plan_path).parent / "api_log.jsonl")
    tokens_in = sum(int(r.get("prompt_tokens") or 0) for r in rows
                    if r.get("api") == "chat")
    tokens_out = sum(int(r.get("completion_tokens") or 0) for r in rows
                     if r.get("api") == "chat")
    search = sum(1 for r in rows if r.get("api") == "search"
                 and (r.get("status") in (None, 200)))
    fetch = sum(1 for r in rows if r.get("api") == "fetch"
                and (r.get("status") in (None, 200)))
    # 引用核验也走 Fetch，单独记在 citation_log
    for r in _read_jsonl(run_dir / "citation_log.jsonl"):
        if r.get("ok") or r.get("status") == 200:
            fetch += 1
    return {"tokens_in_miss": tokens_in, "tokens_in_hit": 0,
            "tokens_out": tokens_out,
            "search_calls": search, "fetch_calls": fetch}


def _image_dir(run_dir: Path) -> Path:
    return run_dir / "images"


def _images_for(state: dict, run_dir: Path, tid: str) -> dict:
    """按部件列出图片文件（相对 run 目录）。"""
    out: dict[str, list[str]] = {}
    meta = state.get("asset_meta") or {}
    for part, ids in ((state.get("assets") or {}).get(tid) or {}).items():
        files = []
        for aid in ids or []:
            m = meta.get(aid) or {}
            img = m.get("image") or ""
            if not img:
                model_dir = run_dir / "images"
                for cand in model_dir.glob(f"*/{aid}.jpg"):
                    img = str(cand.relative_to(run_dir)).replace("\\", "/")
                    break
            if img:
                files.append(img)
        out[part] = files
    return out


def build_manifest(run_dir: Path, brief_path: Path | None = None,
                   plan_path: Path | None = None) -> dict:
    run_dir = Path(run_dir)
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    delivery = summary.get("delivery") or {}
    targets = state.get("targets") or {}

    delivered = []
    for unit_id, tids in (summary.get("accepted_targets") or {}).items():
        for tid in tids:
            t = targets.get(tid) or {}
            delivered.append({
                "model": t.get("model") or tid,
                "unit": unit_id,
                "role": t.get("role", ""),
                "intent_rank": t.get("intent_rank", 0),
                "degraded": tid in (delivery.get("degraded_targets") or []),
                "citation_only": tid in (delivery.get("citation_only_targets") or []),
                "images": _images_for(state, run_dir, tid),
            })
    backup = []
    for tid in ((delivery.get("backup") or {}).get("models") or []):
        t = targets.get(tid) or {}
        backup.append({"model": t.get("model") or tid,
                       "role": t.get("role", ""),
                       "intent_rank": t.get("intent_rank", 0),
                       "images": _images_for(state, run_dir, tid)})

    brief = json.loads(Path(brief_path).read_text(encoding="utf-8")) if brief_path else {}
    usage = collect_usage(run_dir, plan_path)
    cost = pricing.both_cases(usage)

    return {
        "run_id": summary.get("run_id"),
        "state": summary.get("state"),
        "generated_from": str(run_dir).replace("\\", "/"),
        "brief": {
            "id": brief.get("brief_id"),
            "request": brief.get("request"),
            "parts": [p.get("label") or p.get("part")
                      for p in brief.get("part_requirements", [])],
            "slots": (brief.get("request") or {}).get("page_budget", {}).get("vehicle_slots"),
            "backup_slots": (brief.get("request") or {}).get("page_budget", {}).get("backup_slots", 4),
            "source": str(brief_path) if brief_path else "",
        },
        "user_delivery": {
            "delivered": delivered,
            "backup": backup,
            "summary": {k: delivery.get(k) for k in
                        ("required", "delivered", "missing", "degraded",
                         "citation_only", "status")},
        },
        "monitoring": {
            "downloads": summary.get("downloads") or {},
            "unavailable": delivery.get("unavailable") or [],
            "timings": summary.get("timings") or [],
            "elapsed_ms": summary.get("elapsed_ms"),
            "cost_cny": cost,
            "usage": usage,
        },
        "reusable": {
            "brief_json": str(brief_path) if brief_path else "",
            "plan_json": str(plan_path) if plan_path else "",
            "audit_html": str(run_dir / "audit.html") if (run_dir / "audit.html").exists() else "",
            "evidence_db": str(run_dir / "evidence.db") if (run_dir / "evidence.db").exists() else "",
            "part_images": "见 user_delivery.*.images（按 part 分组，可作分析/知识库候选）",
        },
    }


def render_md(m: dict) -> str:
    d = m["user_delivery"]
    s = d["summary"]
    lines = [
        f"# 交付清单：{m['run_id']}",
        "",
        f"> 任务单：`{m['brief'].get('id') or '?'}` · 主 {m['brief'].get('slots')} 台 + 备选 "
        f"{m['brief'].get('backup_slots')} 台 · 状态 {m['state']}",
        f"> 交付 {s.get('delivered')}/{s.get('required')} · degraded {s.get('degraded')} · "
        f"citation_only {s.get('citation_only')} · 备选 {len(d['backup'])} 台",
        "",
        "## 一、用户交付物",
        "",
        "| # | 车型 | 优先级 | 名次 | 图 | 标记 |",
        "|---:|---|---|---:|---:|---|",
    ]
    for i, row in enumerate(d["delivered"], 1):
        n = sum(len(v) for v in row["images"].values())
        tags = []
        if row["degraded"]:
            tags.append("degraded")
        if row["citation_only"]:
            tags.append("citation_only")
        lines.append(f"| {i} | {row['model']} | {row['role'] or '—'} | "
                     f"{row['intent_rank'] or '—'} | {n} | {'/'.join(tags) or '—'} |")
    if d["backup"]:
        lines += ["", "**备选（随包）**：", ""]
        for i, row in enumerate(d["backup"], 1):
            n = sum(len(v) for v in row["images"].values())
            lines.append(f"- {i}. {row['model']}（role={row['role'] or '—'}，rank={row['intent_rank'] or '—'}，{n} 图）")

    mon = m["monitoring"]
    cost = mon["cost_cny"]
    lines += [
        "",
        "## 二、内部监控（不对用户）",
        "",
        f"- 下载：hits {mon['downloads'].get('hits')} / downloaded {mon['downloads'].get('downloaded')} / "
        f"failed {mon['downloads'].get('failed')} / blocked {mon['downloads'].get('blocked')} / "
        f"gate_pass {mon['downloads'].get('gate_pass')}",
        f"- 缺图归因：{_reason_counts(mon['unavailable'])}",
        f"- 总耗时：{mon.get('elapsed_ms')} ms",
        "",
        "| 节点 | 耗时(ms) |",
        "|---|---:|",
    ]
    for t in mon["timings"]:
        lines.append(f"| {t.get('state')} | {t.get('ms')} |")
    lines += [
        "",
        "**API 成本（同一份用量，两种时段口径）**",
        "",
        "| 口径 | chat | Search/Fetch | 合计 |",
        "|---|---:|---:|---:|",
        f"| 全高峰 | ¥{cost['peak']['chat']} | ¥{cost['peak']['api_calls']} | **¥{cost['peak']['total']}** |",
        f"| 全空闲 | ¥{cost['off_peak']['chat']} | ¥{cost['off_peak']['api_calls']} | **¥{cost['off_peak']['total']}** |",
        "",
        f"用量：输入 {mon['usage']['tokens_in_miss']} tokens（按未命中计，偏保守）/ "
        f"输出 {mon['usage']['tokens_out']} / Search {mon['usage']['search_calls']} 次 / "
        f"Fetch {mon['usage']['fetch_calls']} 次",
        "",
        "## 三、可复用中间产物（给其它环节）",
        "",
        f"- 任务单：`{m['reusable']['brief_json']}`（分析模块输入）",
        f"- 优先级先验：`{m['reusable']['plan_json']}`",
        f"- 审核页：`{m['reusable']['audit_html']}`",
        f"- 证据库：`{m['reusable']['evidence_db']}`",
        "- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）",
        "",
    ]
    return "\n".join(lines)


def _reason_counts(rows: list[dict]) -> str:
    counts: dict[str, int] = {}
    for r in rows:
        k = r.get("reason") or "unknown"
        counts[k] = counts.get(k, 0) + 1
    return " / ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "—"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--brief", default="")
    ap.add_argument("--plan", default="")
    args = ap.parse_args(argv)
    run_dir = Path(args.run)
    m = build_manifest(run_dir,
                       Path(args.brief) if args.brief else None,
                       Path(args.plan) if args.plan else None)
    (run_dir / "DELIVERY.json").write_text(
        json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    (run_dir / "DELIVERY.md").write_text(render_md(m), encoding="utf-8")
    print(json.dumps({"run": m["run_id"], "delivered": len(m["user_delivery"]["delivered"]),
                      "backup": len(m["user_delivery"]["backup"]),
                      "cost_peak": m["monitoring"]["cost_cny"]["peak"]["total"],
                      "cost_off": m["monitoring"]["cost_cny"]["off_peak"]["total"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
