# -*- coding: utf-8 -*-
"""T18-roster 轻型吊车补爬：放宽锚点过滤（车型代码分词）+ Bing RSS 兜底。

原因: 首跑 SERP 标题多用型号代码（"QY25K5C"）而非全名（"徐工QY25K5C"），
pick_anchors 的完整名相关词过滤把有效锚点全部误杀，仅 3 篇落盘且均无关。

用法: PYTHONPATH=src python tmp/recrawl_craneL.py
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from crawl4ai import AsyncWebCrawler  # noqa: E402

from equiplens import corpus, webchannel  # noqa: E402
from equiplens.roster import _baidu_serp_url  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data-test" / "corpus" / "batch-corpus-roster-轻型吊车-20261030"
SKIP = ["docin.com", "baike.baidu.com", "b2b.baidu.com"]

VEHICLES = ["徐工QY25K5C", "徐工XCT8L4", "雷萨FTC25X5", "三一STC800C6",
            "雷萨FTC55X5", "徐工QY16KC", "三一QY25C", "三一STC550C5",
            "三一STC1300C8", "徐工QY25K5F", "中联重科ZTC250A"]


def code_terms() -> list[str]:
    """相关词 = 全名 + 品牌 + 型号代码（正则抽取）。"""
    terms = list(VEHICLES) + ["随车吊", "汽车起重机", "起重机", "吊车", "随车起重"]
    for v in VEHICLES:
        terms += re.findall(r"[A-Z]{2,4}\d{2,4}[A-Z0-9]*", v)
    return sorted(set(terms), key=len, reverse=True)


QUOTA = {"review": 10, "industry": 6, "design_media": 2, "official": 2,
         "academic": 2}


async def main() -> None:
    queries = {
        "review": [f"{v} 外观 评测 设计" for v in VEHICLES],
        "industry": [f"{v} 造型 设计语言" for v in VEHICLES],
        "design_media": ["随车吊 造型 设计", "小型起重机 外观 设计"],
        "official": ["徐工起重机 官方网站 随车吊", "三一起重机 官方网站"],
        "academic": ["汽车起重机 驾驶室 设计", "工程机械 工业设计 趋势"],
    }
    all_q = [(st, q) for st, qs in queries.items() for q in qs]
    terms = code_terms()

    async with AsyncWebCrawler(headless=True, verbose=False) as b:
        serp = {}

        async def one(q):
            try:
                r = await b.arun(url=_baidu_serp_url(q))
                return q, (r.markdown if isinstance(r.markdown, str)
                           else str(r.markdown)) if getattr(r, "success", False) else ""
            except Exception:  # noqa: BLE001
                return q, ""

        raw = await asyncio.gather(*[one(q) for _, q in all_q])
        serp = {q: md for q, md in raw}
        blocked = [q for q in serp if corpus.serp_looks_blocked(serp[q])]
        print(f"SERP {len(serp)} 查询, 被拦 {len(blocked)} → Bing 兜底")
        if blocked:
            serp.update(await asyncio.to_thread(corpus._bing_serps, blocked))

        seen = set()
        idx = 1
        index = []
        # 首跑已落盘的 URL 不再重复
        old = OUT / "index.json"
        if old.exists():
            for r in json.loads(old.read_text(encoding="utf-8"))["index"]:
                seen.add(r["url"])

        for st in corpus.SOURCE_TYPES:
            got, quota = 0, QUOTA.get(st, 0)
            per_q = {}
            for st_, q in all_q:
                if st_ != st:
                    continue
                per_q[q] = corpus.pick_anchors(serp.get(q, ""), 3, seen,
                                               relevant_terms=terms)
            cols = [a[:3] for a in per_q.values() if a]
            flat = []
            for i in range(max((len(c) for c in cols), default=0)):
                for col in cols:
                    if i < len(col):
                        flat.append(col[i])
            for a in flat:
                if got >= quota:
                    break
                seen.add(a["url"])
                rec = {"source_type": st, "query": "", "title": a["title"],
                       "url": a["url"], "status": "", "chars": 0, "file": ""}
                index.append(rec)
                real = corpus.resolve_redirect(a["url"])
                rec["url"] = real
                host = (urlparse(real).hostname or "").lower()
                if any(host == d or host.endswith("." + d) for d in SKIP):
                    rec["status"] = "source_skipped"
                    continue
                if not webchannel.robots_allows(real):
                    rec["status"] = "robots_denied"
                    continue
                time.sleep(webchannel.SLEEP_SECONDS)
                try:
                    r = await b.arun(url=real)
                except Exception as e:  # noqa: BLE001
                    rec["status"] = f"fetch_error: {type(e).__name__}"
                    continue
                if not getattr(r, "success", False):
                    rec["status"] = "fetch_failed"
                    continue
                body = r.markdown if isinstance(r.markdown, str) else str(r.markdown)
                md_meta = getattr(r, "metadata", None)
                if isinstance(md_meta, dict) and md_meta.get("title"):
                    rec["title"] = str(md_meta["title"]).strip()[:60]
                rec["chars"] = len(body)
                if len(body) < corpus.MIN_CHARS:
                    rec["status"] = "too_short"
                    continue
                rec["robots"] = "allow"
                rec["fetched_at"] = datetime.now().isoformat(timespec="seconds")
                rec["file"] = corpus.write_doc(OUT, 100 + idx, rec, body).name
                rec["status"] = "saved"
                idx += 1
                got += 1

    # 合并进原 index.json
    data = json.loads(old.read_text(encoding="utf-8"))
    data["index"].extend(index)
    data["plan"]["recrawl"] = "2026-10-30 code-terms + bing-fallback"
    old.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    saved = sum(1 for r in index if r["status"] == "saved")
    print(f"补爬完成: 本轮 {saved}/{len(index)} 落盘")


if __name__ == "__main__":
    asyncio.run(main())
