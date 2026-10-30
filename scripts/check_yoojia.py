# -*- coding: utf-8 -*-
"""定向验证 yoojia.com：已知文章直接抓 + Bing 补链，测设计文本产出稳定性。

用法: PYTHONPATH=src python tmp/check_yoojia.py
输出: data-test/evals/domain-bench-20261030-r2/yoojia-check.{json,md}
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crawl4ai import AsyncWebCrawler  # noqa: E402

from equiplens import corpus, passage, webchannel  # noqa: E402

OUT = ROOT / "data-test" / "evals" / "domain-bench-20261030-r2"
KNOWN = [
    "https://www.yoojia.com/article/9605581790601358817.html",
    "https://www.yoojia.com/dongtai/9257678002",
]
BING_QUERIES = ["有驾 重卡 设计 文章", "有驾 汽车 CMF 设计"]


async def main() -> None:
    urls = list(KNOWN)
    bing = await asyncio.to_thread(corpus._bing_serps, BING_QUERIES)
    for q, md in bing.items():
        for a in corpus.pick_anchors(md, 5, set(urls),
                                     relevant_terms=["yoojia", "有驾", "设计"]):
            if "yoojia.com" in a["url"]:
                urls.append(a["url"])
    urls = list(dict.fromkeys(urls))[:5]

    rows = []
    async with AsyncWebCrawler(headless=True, verbose=False) as b:
        for u in urls:
            if not webchannel.robots_allows(u):
                rows.append({"url": u, "status": "robots_denied", "chars": 0,
                             "a_chars": 0})
                continue
            time.sleep(webchannel.SLEEP_SECONDS)
            try:
                r = await b.arun(url=u)
            except Exception as e:  # noqa: BLE001
                rows.append({"url": u, "status": f"fetch_error: {type(e).__name__}",
                             "chars": 0, "a_chars": 0})
                continue
            if not getattr(r, "success", False):
                rows.append({"url": u, "status": "fetch_failed", "chars": 0,
                             "a_chars": 0})
                continue
            body = r.markdown if isinstance(r.markdown, str) else str(r.markdown)
            g = passage.grade_text(body, "medium")
            rows.append({"url": u, "status": "saved", "chars": len(body),
                         "a_chars": g["a_chars"]})

    body = sum(r["chars"] for r in rows if r["status"] == "saved")
    a = sum(r["a_chars"] for r in rows if r["status"] == "saved")
    saved = sum(1 for r in rows if r["status"] == "saved")
    res = {"pages": len(rows), "saved": saved, "body_chars": body,
           "a_chars": a, "a_per_kchar": round(a / body * 1000, 2) if body else 0.0,
           "a_share": round(a / body, 4) if body else 0.0, "rows": rows}
    (OUT / "yoojia-check.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# yoojia.com 定向验证", "",
          f"- 抓取 {res['pages']} 页（成功 {res['saved']}）｜ 正文 {body:,} 字 / "
          f"A {a:,} 字 → **A/千字 {res['a_per_kchar']}**（A 占比 "
          f"{res['a_share']*100:.1f}%）", "",
          "| URL | 状态 | 正文字 | A 字 |", "|---|---|---:|---:|"]
    for r in rows:
        md.append(f"| {r['url'][:70]} | {r['status']} | {r['chars']} | "
                  f"{r['a_chars']} |")
    (OUT / "yoojia-check.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"yoojia: {saved}/{res['pages']} 成功，A/千字 {res['a_per_kchar']}，"
          f"正文 {body} 字")


if __name__ == "__main__":
    asyncio.run(main())
