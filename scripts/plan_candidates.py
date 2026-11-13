# -*- coding: utf-8 -*-
"""候选规划：任务单 → 查询计划 → 逐条 Search + 逐条抽取 → 带出处的候选池。

流程（v2-provenance，2026-11-11）：
  1) `equiplens.planning.build_query_plan` 生成查询计划（query_id/dimension/purpose）
  2) 每条查询单独 Search，结果只属于这条查询
  3) 每条查询单独让 LLM 抽候选，候选必须绑定本查询结果里的 URL
  4) `validate_extraction` 校验 URL，`merge_candidates` 合并同车型并保留来源查询
  5) `coverage_report` 报“哪个维度有货/哪个维度空”

只用 DeepSeek 一个 key（Chat + Search）。用法:
  python scripts/plan_candidates.py --brief <brief.json> --out <plan.json>
  # 覆盖实验：只加市场段/工况描述，不写品牌名单
  python scripts/plan_candidates.py ... --extra-query "进口 沙漠牵引车 6×6 车型"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens.planning import (auto_limits, build_query_plan, coverage_report,  # noqa: E402
                                dedupe_stats, merge_candidates,
                                pool_requirement, pool_warning, top_up_queries,
                                validate_extraction)

API = "https://api.deepseek.com"
KEY_FILE = Path.home() / ".equiplens" / "deepseek.env"


def load_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("DEEPSEEK_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no DEEPSEEK_API_KEY")


def search(key: str, query: str, count: int = 20) -> list[dict]:
    r = requests.post(f"{API}/v1/tools/search",
                      headers={"Authorization": f"Bearer {key}",
                               "Content-Type": "application/json"},
                      json={"query": query, "count": count}, timeout=60)
    r.raise_for_status()
    return r.json().get("results", [])


def extract(key: str, brief: dict, query_meta: dict, results: list[dict],
            want: int = 6) -> tuple[dict, dict]:
    """只从**这一条查询**的结果里抽候选，避免跨查询混池。"""
    compact = [{"title": r.get("title", ""), "url": r.get("url", ""),
                "summary": (r.get("summary") or r.get("snippet") or "")[:280]}
               for r in results]
    prompt = (
        "你是工程车/重卡检索规划助手。下面是一组关于查询"
        f"「{query_meta['query']}」的检索结果。\n"
        f"请只从这些结果里抽最多 {want} 个候选车型（品牌 + 车系/型号），要求：\n"
        "1) 只能从给出的结果里推断，不允许凭记忆补充；\n"
        "2) 每条候选必须给出至少 1 个来源 URL，且 URL 必须来自下面结果；\n"
        "3) 同一车型只给一次；与任务单环境/构型不符的不要；\n"
        "4) 输出 JSON：{\"candidates\":[{\"model\":\"\",\"brand\":\"\","
        "\"reason\":\"\",\"sources\":[\"url\"]}]}。\n\n"
        f"任务单：{json.dumps(brief.get('request', {}), ensure_ascii=False)}\n"
        f"检索结果：{json.dumps(compact, ensure_ascii=False)}"
    )
    r = requests.post(f"{API}/chat/completions",
                      headers={"Authorization": f"Bearer {key}",
                               "Content-Type": "application/json"},
                      json={"model": "deepseek-flash",
                            "messages": [{"role": "user", "content": prompt}],
                            "response_format": {"type": "json_object"},
                            "temperature": 0},
                      timeout=180)
    r.raise_for_status()
    data = r.json()
    return json.loads(data["choices"][0]["message"]["content"]), (data.get("usage") or {})


def run_query(key: str, brief: dict, meta: dict, want: int,
              sleep_s: float = 0.3) -> dict:
    """一条查询 = 1 次 Search + 1 次抽取；只依赖本查询自己的结果（可并发）。"""
    q = meta["query"]
    api: list[dict] = []
    extracted: list[dict] = []
    t0 = time.time()
    try:
        res = search(key, q, 20)
    except Exception as e:  # noqa: BLE001
        print(f"search fail {q}: {type(e).__name__}")
        res = []
    row = {**meta, "results": len(res)}
    api.append({"api": "search", "query_id": meta["query_id"],
                "dimension": meta["dimension"], "query": q,
                "results": len(res), "billable": bool(res),
                "ms": round((time.time() - t0) * 1000),
                "cost_usd": 0.00075 if res else 0})
    if res:
        t1 = time.time()
        try:
            got, usage = extract(key, brief, meta, res, want)
            api.append({"api": "chat", "model": "deepseek-flash",
                        "query_id": meta["query_id"],
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "ms": round((time.time() - t1) * 1000),
                        "billable": True})
            rows, stats = validate_extraction(
                got, {str(r.get("url") or "") for r in res}, meta, want)
            row.update(stats)
            extracted.extend(rows)
        except Exception as e:  # noqa: BLE001
            print("extract fail", meta["query_id"], type(e).__name__, str(e)[:160])
            row.update({"kept": 0, "error": type(e).__name__})
    time.sleep(sleep_s)
    return {"row": row, "api": api, "extracted": extracted, "res": res}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0,
                    help="候选池总上限；0=按 1.6×(slots+backup) 自动（2026-11-12）")
    ap.add_argument("--topup", type=int, default=2,
                    help="候选池不足时追加的查询数（默认 2，0=关闭；最多 2）")
    ap.add_argument("--per-query", type=int, default=0,
                    help="每条查询最多抽几个候选；0=按目标池/查询数自动")
    ap.add_argument("--extra-query", action="append", default=[],
                    help="额外的覆盖查询（只写市场段/工况，不写品牌名单；可重复）")
    ap.add_argument("--no-negative", action="store_true",
                    help="A/B 用：查询不追加 -\"短词\"（brief 不变，其余逐字相同）")
    ap.add_argument("--concurrency", type=int, default=4,
                    help="查询并发数；默认 4=生产（A 测试 3.3×），1=串行对照臂")
    args = ap.parse_args(argv)

    key = load_key()
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    query_plan = build_query_plan(brief, args.extra_query,
                                  use_negative=not args.no_negative)
    page_budget = (brief.get("request") or {}).get("page_budget") or {}
    slots = int(page_budget.get("vehicle_slots") or 0)
    backup = page_budget.get("backup_slots")
    backup = 4 if backup is None else int(backup)
    limits = auto_limits(slots, backup, n_queries=len(query_plan),
                         per_query=args.per_query, limit=args.limit)
    extract_n = limits["per_query"]   # 每条查询最多抽几个（标量，别和下面的结果列表重名）

    all_results: list[dict] = []
    per_query: list[dict] = []
    api_rows: list[dict] = []
    extracted: list[dict] = []

    def run_batch(batch: list[dict]) -> list[dict]:
        if int(args.concurrency or 1) > 1:
            with ThreadPoolExecutor(max_workers=int(args.concurrency)) as ex:
                return list(ex.map(
                    lambda m: run_query(key, brief, m, extract_n), batch))
        return [run_query(key, brief, m, extract_n) for m in batch]

    def absorb(outs: list[dict]) -> None:
        for out in outs:
            per_query.append(out["row"])
            api_rows.extend(out["api"])
            all_results.extend(out["res"])
            extracted.extend(out["extracted"])

    absorb(run_batch(query_plan))

    topup_rows: list[dict] = []
    extras: list[dict] = []
    if int(args.topup or 0) > 0:
        merged_so_far = merge_candidates(extracted)
        if len(merged_so_far) < limits["need"]:
            extras = top_up_queries(brief, [q["query"] for q in query_plan],
                                    max_extra=min(2, int(args.topup)))
            outs = run_batch(extras)
            absorb(outs)
            topup_rows = [o["row"] for o in outs]

    seen: set[str] = set()
    uniq: list[dict] = []
    for r in all_results:
        u = str(r.get("url") or "")
        if u and u not in seen:
            seen.add(u)
            uniq.append(r)

    merged_all = merge_candidates(extracted)
    need = limits["need"]
    candidates = merged_all[:limits["limit"]]
    warn = pool_warning(len(candidates), slots, backup)
    if warn:
        print("WARN " + warn, file=sys.stderr)
    plan = {
        "brief_id": brief.get("brief_id"),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "deepseek-flash",
        "planner_version": "v2-provenance",
        "concurrency": int(args.concurrency or 1),
        "queries": per_query,
        "search_results": len(uniq),
        "candidates": candidates,
        "topup": {"enabled": int(args.topup or 0), "queries": len(extras),
                  "kept": sum(int(x.get("kept") or 0) for x in topup_rows),
                  "candidates_before": len(merge_candidates(extracted)) if not extras else None},
        "pool": {"count": len(candidates), "required": need,
                 "slots": slots, "backup": backup,
                 "per_query": extract_n, "limit": limits["limit"],
                 "ok": not warn, "warning": warn},
        "coverage": coverage_report(query_plan, candidates,
                                     slots=((brief.get("request") or {}).get("page_budget") or {}).get("vehicle_slots")),
        "dedupe": dedupe_stats(extracted, candidates),
        "dropped_without_valid_source": sum(int(q.get("dropped_no_source") or 0)
                                            for q in per_query),
        "dropped_invalid_sources": sum(int(q.get("dropped_invalid_source") or 0)
                                       for q in per_query),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    with (out.parent / "api_log.jsonl").open("w", encoding="utf-8") as f:
        for row in api_rows:
            f.write(json.dumps(row, ensure_ascii=False) + chr(10))
    print(json.dumps({"queries": len(query_plan), "search_results": len(uniq),
                      "candidates": len(candidates),
                      "dropped_no_source": plan["dropped_without_valid_source"],
                      "dropped_invalid": plan["dropped_invalid_sources"],
                      "coverage_missing": plan["coverage"]["missing"],
                      "pool_ok": plan["pool"]["ok"],
                      "pool_required": plan["pool"]["required"]},
                     ensure_ascii=False))
    print("out:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
