# -*- coding: utf-8 -*-
"""运行台账：扫描 data-test/runs，生成 RUN.json + INDEX.json / INDEX.md。

约定：
- 一个实验目录 = 一条记录；`RUN.json` 是机器可读的“这一轮是什么”；
- `INDEX.json` / `INDEX.md` 只由本脚本生成，不手改；
- 不删除任何目录；空目录 / 嵌套旧目录只标记 `kind=empty` / `archived`。

用法:
  python scripts/run_ledger.py --check          # 只检查，不写
  python scripts/run_ledger.py --write          # 补 RUN.json + 重建索引
  python scripts/run_ledger.py --write --force  # 覆盖已有 RUN.json（会丢手写结论）
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data-test" / "runs"
STAGES = (
    ("filter", "gate"),
    ("web-smoke", "search"),
    ("web-reassess", "gate"),
    ("loop", "loop"),
    ("plan", "plan"),
    ("run-", "text-retrieval"),
    ("T18", "eval"),
    ("p1", "engine"),
    ("diag", "search"),
)


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=ROOT, text=True).strip()
    except Exception:  # noqa: BLE001
        return ""


def _date(name: str, mtime: float, summary: dict | None = None,
          state: dict | None = None) -> str:
    m = re.search(r"(20\d{6})", name)
    if m:
        s = m.group(1)
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    for src in (state or {}, summary or {}):
        for key in ("updated_at", "finished_at", "run_at", "created_at",
                    "started_at", "ended_at"):
            val = str(src.get(key) or "")
            if re.match(r"20\d{2}-\d{2}-\d{2}", val):
                return val[:10]
    return time.strftime("%Y-%m-%d", time.localtime(mtime))


def _stage(name: str) -> str:
    for prefix, stage in STAGES:
        if name.startswith(prefix) or prefix in name:
            return stage
    return "other"


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_jsonl(path: Path, limit: int | None = None) -> list[dict]:
    rows = []
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                if limit and len(rows) >= limit:
                    break
    except OSError:
        pass
    return rows


def _conclusion_from_report(path: Path, limit: int = 200) -> str:
    """优先取报告里的“结论”段；没有就取一级标题；都没有才取第一段正文。"""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"##+\s*结论[^\n]*\n+(.+?)(?:\n\s*\n|\Z)", text, re.S)
    if m:
        return " ".join(m.group(1).split())[:limit]
    heading = re.search(r"^#\s+(.+)$", text, re.M)
    if heading:
        return heading.group(1).strip()[:limit]
    for block in re.split(r"\n\s*\n", text):
        lines = [x.strip() for x in block.splitlines() if x.strip()]
        if not lines or lines[0].startswith(("#", ">", "|")):
            continue
        return " ".join(lines)[:limit]
    return ""


def _run_metrics(path: Path, summary: dict | None, state: dict | None) -> dict:
    metrics: dict = {}
    if summary:
        metrics["state"] = summary.get("state")
        delivery = summary.get("delivery") or {}
        if delivery:
            metrics["delivery"] = f"{delivery.get('delivered')}/{delivery.get('required')}"
            metrics["degraded"] = delivery.get("degraded")
            metrics["citation_only"] = delivery.get("citation_only")
            metrics["bonus_images"] = (delivery.get("bonus") or {}).get("images")
            b = delivery.get("backup") or {}
            if b:
                metrics["backup"] = f"{b.get('delivered')}/{b.get('required')}"
        coverage = summary.get("coverage") or {}
        if coverage:
            metrics["coverage"] = {k: f"{v.get('accepted')}/{v.get('quota')}"
                                   for k, v in coverage.items() if isinstance(v, dict)}
    if not metrics and state:
        metrics["state"] = state.get("final_state") or state.get("state")
        metrics["targets"] = len(state.get("targets") or {})
    log = path / "fetch_log.jsonl"
    if log.exists():
        rows = _read_jsonl(log)
        ok = [r for r in rows if r.get("ok")]
        metrics["images"] = len({r.get("sha1") for r in ok})
        metrics["gate_pass"] = len({r.get("sha1") for r in ok if r.get("gate_pass")})
        metrics["download_failed"] = sum(1 for r in rows if not r.get("ok"))
    api = path / "api_log.jsonl"
    if api.exists():
        rows = _read_jsonl(api)
        metrics["api_calls"] = len(rows)
        metrics["api_cost_usd"] = round(sum(float(r.get("cost_usd") or 0) for r in rows), 5)
    return metrics


def _plan_metrics(plan: dict) -> dict:
    cov = plan.get("coverage") or {}
    dd = plan.get("dedupe") or {}
    return {
        "queries": len(plan.get("queries") or []),
        "search_results": plan.get("search_results"),
        "candidates": len(plan.get("candidates") or []),
        "dedupe_removed": dd.get("removed"),
        "pool_shortfall": cov.get("pool_shortfall"),
        "coverage_missing": cov.get("missing"),
    }


def _looks_auto(text: str, record: dict) -> bool:
    """判断一条结论是不是旧版台账自动生成的（用于迁移）。"""
    t = (text or "").strip()
    if not t:
        return False
    status = str(record.get("status") or "")
    if status and t == status:
        return True
    if t == "无结论":
        return True
    if status and re.fullmatch(rf"{re.escape(status)} \d+/\d+（degraded=[^）]*）", t):
        return True
    if re.fullmatch(r"候选 \S+ / 查询 \S+ / 去重移除 \S+", t):
        return True
    if re.fullmatch(r"\d+ 个 plan", t):
        return True
    return False


def _auto_conclusion(record: dict, kind: str, plan_count: int) -> str:
    """机器统计出的摘要。**不是**人工结论，只写 auto_conclusion。"""
    m = record.get("metrics") or {}
    if kind == "run":
        if m.get("delivery"):
            return f"{record['status']} {m['delivery']}（degraded={m.get('degraded', '?')}）"
        return record["status"] or "无结论"
    if kind == "plan":
        removed = m.get("dedupe_removed")
        return (f"候选 {m.get('candidates', '?')} / 查询 {m.get('queries', '?')}"
                f" / 去重移除 {removed if removed is not None else '—'}")
    if kind == "plan-set":
        return f"{plan_count} 个 plan"
    return ""


def build_record(path: Path) -> dict:
    name = path.name
    mtime = path.stat().st_mtime
    summary = _read_json(path / "summary.json")
    state = _read_json(path / "state.json")
    plan = _read_json(path / "plan.json")
    children = [d for d in sorted(path.iterdir()) if d.is_dir() and (d / "plan.json").exists()]
    existing = _read_json(path / "RUN.json") or {}

    if plan:
        kind = "plan"
    elif children:
        kind = "plan-set"
    elif summary or state:
        kind = "run"
    elif (path / "fetch_log.jsonl").exists() or (path / "events.jsonl").exists():
        kind = "diag"
    elif name == "runs":
        kind = "archived"
    else:
        kind = "empty"

    report = next((p for p in (path / "REPORT.md", path / "report.md",
                               path / "report.json", path / "README.md")
                   if p.exists()), None)
    record = {
        "run_id": name,
        "kind": kind,
        "stage": _stage(name),
        "date": _date(name, mtime, summary, state),
        "status": (summary or {}).get("state") or (state or {}).get("final_state") or "",
        "brief_id": (summary or {}).get("brief_id") or "",
        "git_commit": _git_commit(),
        "metrics": _plan_metrics(plan) if plan else _run_metrics(path, summary, state),
        "report": str(report.relative_to(ROOT)) if report else "",
        "summary": "data-test/runs/" + name + "/summary.json" if summary else "",
        "audit": "data-test/runs/" + name + "/audit.html"
                 if (path / "audit.html").exists() else "",
        "conclusion": existing.get("conclusion", ""),
        "auto_conclusion": existing.get("auto_conclusion", ""),
        "conclusion_source": existing.get("conclusion_source", ""),
        "generated_by": "scripts/run_ledger.py",
    }
    if kind == "plan-set":
        record["plans"] = [d.name for d in children]
        record["metrics"] = {"plans": len(children)}
    # 旧版台账把机器统计写进 conclusion，然后用它把 needs_review 清成 false。
    # 迁移：可识别的机器结论移到 auto_conclusion；conclusion 只留人工/报告来源。
    if record["conclusion"] and _looks_auto(record["conclusion"], record):
        record["auto_conclusion"] = record["auto_conclusion"] or record["conclusion"]
        record["conclusion"] = ""
    if record["conclusion"]:
        record["conclusion_source"] = record.get("conclusion_source") or "stored"
    elif report:
        text = _conclusion_from_report(report)
        if text:
            record["conclusion"] = text
            record["conclusion_source"] = "report"
    if not record["conclusion"]:
        record["auto_conclusion"] = record["auto_conclusion"] or _auto_conclusion(
            record, kind, len(children))
        record["conclusion_source"] = record["conclusion_source"] or "auto"
    # 待复核 = 没有人工结论；机器摘要不能自证已复核。
    record["needs_review"] = not bool(record["conclusion"])
    # 只保留人工写的备注；conclusion 已在上面按来源处理过，不能再用旧值覆盖。
    for key in ("notes",):
        if existing.get(key):
            record[key] = existing[key]
    for key in ("report", "summary", "audit"):
        if record.get(key):
            record[key] = record[key].replace("\\", "/")
    return record


def scan(root: Path = RUNS) -> list[dict]:
    records = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        records.append(build_record(d))
    return records


def write_manifests(records: list[dict], force: bool = False) -> int:
    written = 0
    for rec in records:
        if rec["kind"] in ("empty", "archived"):
            continue
        path = RUNS / rec["run_id"] / "RUN.json"
        if path.exists() and not force:
            continue
        payload = {k: v for k, v in rec.items()
                   if k not in ("report_title",) and k != "generated_by"}
        payload["generated_by"] = "scripts/run_ledger.py"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        written += 1
    return written


def write_index(records: list[dict]) -> None:
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "root": "data-test/runs",
        "counts": {
            "all": len(records),
            "run": sum(1 for r in records if r["kind"] == "run"),
            "plan": sum(1 for r in records if r["kind"] == "plan"),
            "plan-set": sum(1 for r in records if r["kind"] == "plan-set"),
            "diag": sum(1 for r in records if r["kind"] == "diag"),
            "empty": sum(1 for r in records if r["kind"] == "empty"),
            "needs_review": sum(1 for r in records if r.get("needs_review")),
        },
        "records": records,
    }
    (RUNS / "INDEX.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [
        "# 运行台账（data-test/runs）",
        "",
        "> 由 `scripts/run_ledger.py` 生成，**不要手改**；结论请写在各目录的 `RUN.json.conclusion`"
        " 或 `REPORT.md`。",
        f"> 生成时间：{payload['generated_at']} · 共 {len(records)} 条"
        f" · 待补人工结论 {payload['counts']['needs_review']} 条",
        "",
        "| 阶段 | run_id | 类型 | 日期 | 状态 | 关键指标 | 结论/报告 |",
        "|---|---|---|---|---|---|---|",
    ]
    order = {"loop": 0, "plan": 1, "search": 2, "gate": 3, "eval": 4,
             "engine": 5, "text-retrieval": 6, "other": 7}
    for rec in sorted(records, key=lambda r: (order.get(r["stage"], 9),
                                              r["date"], r["run_id"])):
        if rec["kind"] in ("empty", "archived"):
            continue
        metrics = rec.get("metrics") or {}
        bits = []
        for key in ("delivery", "backup", "candidates", "images", "gate_pass",
                    "degraded", "arc"):
            if key in metrics and metrics[key] not in (None, ""):
                bits.append(f"{key}={metrics[key]}")
        if "api_cost_usd" in metrics:
            bits.append(f"${metrics['api_cost_usd']}")
        conclusion = rec.get("conclusion") or rec.get("report_title") or "—"
        link = rec.get("report") or rec.get("audit") or rec.get("summary") or ""
        cell = f"[{conclusion[:80]}]({link})" if link else conclusion[:80]
        lines.append(
            f"| {rec['stage']} | `{rec['run_id']}` | {rec['kind']} | {rec['date']} | "
            f"{rec['status'] or '—'} | {' · '.join(bits) or '—'} | {cell} |")
    lines += ["", "## 空目录 / 归档", ""]
    for rec in records:
        if rec["kind"] in ("empty", "archived"):
            lines.append(f"- `{rec['run_id']}` → {rec['kind']}（未删除，仅标记）")
    (RUNS / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def check(records: list[dict]) -> int:
    bad = 0
    for rec in records:
        if rec["kind"] in ("empty", "archived"):
            continue
        if not (RUNS / rec["run_id"] / "RUN.json").exists():
            print(f"missing RUN.json: {rec['run_id']} ({rec['kind']})")
            bad += 1
    if not (RUNS / "INDEX.json").exists():
        print("missing INDEX.json")
        bad += 1
    print(f"ledger: {len(records)} records, {bad} issue(s)")
    return 0 if bad == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(RUNS))
    ap.add_argument("--write", action="store_true", help="补 RUN.json 并重建索引")
    ap.add_argument("--force", action="store_true", help="覆盖已有 RUN.json")
    ap.add_argument("--check", action="store_true", help="只检查")
    args = ap.parse_args(argv)
    records = scan(Path(args.root))
    if args.write:
        n = write_manifests(records, force=args.force)
        records = scan(Path(args.root))
        write_index(records)
        print(f"wrote {n} RUN.json; index: {len(records)} records")
    return check(records) if args.check or not args.write else 0


if __name__ == "__main__":
    raise SystemExit(main())
