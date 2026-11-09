"""检索中引擎 CLI（P1/P2-W1，默认夹具；--web-only 走真实网页）。

用法:
  # P1 夹具
  PYTHONPATH=src python -m equiplens.retrieval_engine \
      --brief data-test/retrieval-fixtures-20261109/brief-desert.json \
      --fixtures data-test/retrieval-fixtures-20261109/world-desert.json \
      --run-root data-test/runs --run-id p1-demo

  # P2-W1 网页-only（真实 360，谨慎跑）
  PYTHONPATH=src python -m equiplens.retrieval_engine \
      --brief data-test/retrieval-fixtures-20261109/brief-desert.json \
      --web-only --models "豪沃6X6,德龙X3000" \
      --run-root data-test/runs --run-id web-demo
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from .adapters import FakeWorld
from .contracts import load_brief, load_strategy
from .engine import RetrievalEngine
from .evidence import EvidenceStore
from .web import WebWorld


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="equiplens.retrieval_engine",
                                     description="检索中状态机（P1 夹具 / P2 网页）")
    parser.add_argument("--brief", required=True)
    parser.add_argument("--fixtures", default=None,
                        help="夹具世界（P1）；--web-only 时可省略")
    parser.add_argument("--web-only", action="store_true",
                        help="空库 + 真实网页检索（360）")
    parser.add_argument("--models", default=None,
                        help="网页-only 的型号候选，逗号分隔")
    parser.add_argument("--searxng", default=os.environ.get("SEARXNG_URL"),
                        help="SearXNG 实例 URL（如 http://127.0.0.1:8080）")
    parser.add_argument("--tavily-key", default=os.environ.get("TAVILY_API_KEY"),
                        help="Tavily API key（也可用 TAVILY_API_KEY 环境变量）")
    parser.add_argument("--run-root", default="data-test/runs")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--strategy", default="data/retrieval_strategies.json")
    parser.add_argument("--evidence-db", default=None,
                        help="写入 image_evidence 的 SQLite 路径（可选）")
    parser.add_argument("--json", action="store_true", help="输出完整 JSON")
    args = parser.parse_args(argv)

    run_id = args.run_id or f"p1-{time.strftime('%Y%m%d-%H%M%S')}"
    brief = load_brief(args.brief)
    if args.web_only:
        if not args.models:
            parser.error("--web-only 需要 --models（逗号分隔）")
        router = None
        if args.searxng or args.tavily_key:
            from .sources import (SearchCache, SourceHealth, SourceRouter,
                                  SearxngSource, TavilySource, source_360)
            sources = [("360", source_360)]
            if args.searxng:
                sources.append(("searxng", SearxngSource(args.searxng)))
            if args.tavily_key:
                sources.append(("tavily", TavilySource(args.tavily_key)))
            base = Path(args.run_root) / run_id
            router = SourceRouter(
                sources,
                SourceHealth(base / "source_health.json"),
                SearchCache(base / "source_cache.json"))
        world = WebWorld([m.strip() for m in args.models.split(",") if m.strip()],
                         brief.parts_by_key, router=router)
    else:
        if not args.fixtures:
            parser.error("非 --web-only 需要 --fixtures")
        world = FakeWorld.from_file(args.fixtures)

    strategy = None
    if Path(args.strategy).exists():
        strategy = load_strategy(args.strategy, brief.strategy_ref)

    writer = None
    if args.evidence_db:
        store = EvidenceStore(args.evidence_db)
        writer = lambda rows: store.write_rows(run_id, rows)  # noqa: E731

    engine = RetrievalEngine(brief, world, run_root=args.run_root,
                             run_id=run_id, strategy=strategy,
                             evidence_writer=writer)
    summary = engine.run()
    if args.evidence_db:
        summary["evidence_db"] = args.evidence_db
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"run_id: {summary['run_id']}  state: {summary['state']}")
        for uid, c in summary["coverage"].items():
            print(f"  {uid}: {c['accepted']}/{c['quota']} "
                  f"{'filled' if c['filled'] else 'gap'}")
        if summary["gaps"]:
            print(f"  gaps: {', '.join(summary['gaps'])}")
        print(f"  state: {summary['state_path']}")
        print(f"  events: {summary['events_path']}")
        if args.evidence_db:
            print(f"  evidence_db: {args.evidence_db}")
    return 0 if summary["state"] == "DONE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
