# -*- coding: utf-8 -*-
"""候选规划：任务单 → DeepSeek Search（带引用）→ LLM 抽取候选池。

只用 DeepSeek 一个 key：
  - Search API 取实时结果（title/url/summary/authority）
  - Chat API 从结果里抽取候选车型（JSON），并要求每条候选绑定来源 URL
  - 脚本再校验：候选引用的 URL 必须出现在本次检索结果里（防止模型编链接）

用法:
  python scripts/plan_candidates.py --brief data-test/evals/task-briefs-20261109/brief-m1-desert.json \
      --out data-test/runs/plan-c01/plan.json
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


def build_queries(brief: dict) -> list[str]:
    """任务单 → 查询（不用任何品牌白名单）。

    除 request 的类目/工况，还要覆盖每个 research_unit 的 scope——否则
    “国际品牌”“某工况工程车”这类单元永远不会被搜到（T38 独立测试暴露）。
    """
    req = brief.get("request") or {}
    env = (req.get("environment") or {}).get("value") or ""
    klass = req.get("class") or ""
    conf = req.get("configuration") or ""
    neg = " ".join(f'-"{x}"' for x in (brief.get("negative") or [])[:4])
    base = " ".join(x for x in (env, klass, conf) if x)
    raw = [base, f"{klass} {conf} 车型 品牌", f"{env} {conf} 卡车 车型",
           f"{klass} {conf} truck brands"]
    for unit in brief.get("research_units") or []:
        scope = (unit.get("scope") or "").strip()
        if scope:
            raw.append(f"{scope} {conf}".strip())
    qs: list[str] = []
    for q in raw:
        q = " ".join(q.split())
        if q and q not in qs:
            qs.append(q)
    return [q + (" " + neg if neg else "") for q in qs]


def search(key: str, query: str, count: int = 20) -> list[dict]:
    r = requests.post(f"{API}/v1/tools/search",
                      headers={"Authorization": f"Bearer {key}",
                               "Content-Type": "application/json"},
                      json={"query": query, "count": count}, timeout=60)
    r.raise_for_status()
    return r.json().get("results", [])


def extract(key: str, brief: dict, results: list[dict], want: int = 24) -> dict:
    compact = [{"title": r.get("title", ""), "url": r.get("url", ""),
                "summary": (r.get("summary") or r.get("snippet") or "")[:300],
                "authority": r.get("authority")} for r in results]
    prompt = (
        "你是工程车/重卡检索规划助手。根据任务单和下面这些实时检索结果，"
        f"给出最多 {want} 个候选车型（品牌 + 车系/型号），要求：\n"
        "1) 只能从给出的结果里推断，不允许凭记忆补充；\n"
        "2) 每条候选必须给出至少 1 个来源 URL，且该 URL 必须来自下面的结果；\n"
        "3) 优先与任务单的使用环境/构型一致的车型，包含国产与外国品牌；\n"
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
                            "temperature": 0.2},
                      timeout=180)
    r.raise_for_status()
    data = r.json()
    usage = data.get("usage") or {}
    text = data["choices"][0]["message"]["content"]
    return json.loads(text), usage


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=24)
    args = ap.parse_args(argv)

    key = load_key()
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    queries = build_queries(brief)
    all_results, per_query, api_rows = [], [], []
    for q in queries:
        try:
            res = search(key, q, 20)
        except Exception as e:  # noqa: BLE001
            print(f"search fail {q}: {type(e).__name__}")
            res = []
        per_query.append({"query": q, "results": len(res)})
        api_rows.append({"api": "search", "query": q, "results": len(res),
                         "billable": bool(res), "cost_usd": 0.00075 if res else 0})
        all_results.extend(res)
        time.sleep(0.3)

    # URL 去重
    seen, uniq = set(), []
    for r in all_results:
        u = r.get("url", "")
        if not u or u in seen:
            continue
        seen.add(u)
        uniq.append(r)

    plan = {"brief_id": brief.get("brief_id"), "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "model": "deepseek-flash", "queries": per_query,
            "search_results": len(uniq), "candidates": []}
    if uniq:
        try:
            got, usage = extract(key, brief, uniq, args.limit)
            api_rows.append({"api": "chat", "model": "deepseek-flash",
                             "prompt_tokens": usage.get("prompt_tokens"),
                             "completion_tokens": usage.get("completion_tokens"),
                             "billable": True})
        except Exception as e:  # noqa: BLE001
            print("extract fail", type(e).__name__, str(e)[:200])
            got, usage = {"candidates": []}, {}
        valid_urls = {r["url"] for r in uniq}
        dropped = 0
        for c in got.get("candidates", []):
            srcs = [u for u in (c.get("sources") or []) if u in valid_urls]
            if not srcs:
                dropped += 1
                continue
            model = (c.get("model") or "").strip()
            plan["candidates"].append({
                "model": model,
                "query": (c.get("query") or "").strip(),
                "brand": (c.get("brand") or "").strip(),
                "reason": (c.get("reason") or "").strip()[:200],
                "sources": srcs,
            })
        plan["dropped_without_valid_source"] = dropped

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    with (out.parent / "api_log.jsonl").open("w", encoding="utf-8") as f:
        for row in api_rows:
            f.write(json.dumps(row, ensure_ascii=False) + chr(10))
    print(json.dumps({"queries": len(queries), "search_results": len(uniq),
                      "candidates": len(plan["candidates"]),
                      "dropped": plan.get("dropped_without_valid_source", 0)},
                     ensure_ascii=False))
    print("out:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
