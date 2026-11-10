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
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens.planning import (build_query_plan, coverage_report,  # noqa: E402
                                merge_candidates, validate_extraction)

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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=36, help="候选池总上限")
    ap.add_argument("--per-query", type=int, default=6, help="每条查询最多抽几个候选")
    ap.add_argument("--extra-query", action="append", default=[],
                    help="额外的覆盖查询（只写市场段/工况，不写品牌名单；可重复）")
    args = ap.parse_args(argv)

    key = load_key()
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    query_plan = build_query_plan(brief, args.extra_query)

    all_results: list[dict] = []
    per_query: list[dict] = []
    api_rows: list[dict] = []
    extracted: list[dict] = []
    for meta in query_plan:
        q = meta["query"]
        try:
            res = search(key, q, 20)
        except Exception as e:  # noqa: BLE001
            print(f"search fail {q}: {type(e).__name__}")
            res = []
        row = {**meta, "results": len(res)}
        api_rows.append({"api": "search", "query_id": meta["query_id"],
                         "dimension": meta["dimension"], "query": q,
                         "results": len(res), "billable": bool(res),
                         "cost_usd": 0.00075 if res else 0})
        all_results.extend(res)
        if res:
            try:
                got, usage = extract(key, brief, meta, res, args.per_query)
                api_rows.append({"api": "chat", "model": "deepseek-flash",
                                 "query_id": meta["query_id"],
                                 "prompt_tokens": usage.get("prompt_tokens"),
                                 "completion_tokens": usage.get("completion_tokens"),
                                 "billable": True})
                rows, stats = validate_extraction(
                    got, {str(r.get("url") or "") for r in res}, meta, args.per_query)
                row.update(stats)
                extracted.extend(rows)
            except Exception as e:  # noqa: BLE001
                print("extract fail", meta["query_id"], type(e).__name__, str(e)[:160])
                row.update({"kept": 0, "error": type(e).__name__})
        per_query.append(row)
        time.sleep(0.3)

    seen: set[str] = set()
    uniq: list[dict] = []
    for r in all_results:
        u = str(r.get("url") or "")
        if u and u not in seen:
            seen.add(u)
            uniq.append(r)

    candidates = merge_candidates(extracted)[:args.limit]
    plan = {
        "brief_id": brief.get("brief_id"),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "deepseek-flash",
        "planner_version": "v2-provenance",
        "queries": per_query,
        "search_results": len(uniq),
        "candidates": candidates,
        "coverage": coverage_report(query_plan, candidates),
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
                      "coverage_missing": plan["coverage"]["missing"]},
                     ensure_ascii=False))
    print("out:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
