# -*- coding: utf-8 -*-
"""T18-roster 宏观设计查询补爬（G 档样本）。

缺陷修复：首跑 relevant_terms 强制标题含车型名 → 类目级宏观查询
（"工程机械 工业设计 趋势"等）锚点被全部误杀，G 档为 0。
本脚本不带车型过滤，只跑 4 类目的宏观设计查询，捕获"非指向"参考文本。

用法: PYTHONPATH=src python tmp/recrawl_generic.py
"""
from __future__ import annotations

import asyncio
import json
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

QUERIES = [
    ("沙漠牵引车", "design_media", "油田牵引车 外观 设计"),
    ("沙漠牵引车", "industry", "重型卡车 家族化 设计语言"),
    ("沙漠牵引车", "academic", "工程机械 工业设计 趋势"),
    ("重型吊车", "design_media", "起重机 外观 设计语言"),
    ("重型吊车", "industry", "汽车起重机 造型 设计"),
    ("重型吊车", "academic", "工程机械 工业设计 趋势"),
    ("轻型吊车", "design_media", "随车吊 造型 设计"),
    ("轻型吊车", "industry", "汽车起重机 驾驶室 设计"),
    ("轻型吊车", "academic", "工程机械 工业设计 趋势"),
    ("翻斗铲车", "design_media", "自卸车 造型 设计"),
    ("翻斗铲车", "industry", "矿用卡车 外观 设计"),
    ("翻斗铲车", "academic", "工程机械 工业设计 趋势"),
]
SKIP = ["docin.com", "baike.baidu.com", "b2b.baidu.com"]
QUOTA_PER_CAT = 4


async def main() -> None:
    async with AsyncWebCrawler(headless=True, verbose=False) as b:
        serp = {}

        async def one(q):
            try:
                r = await b.arun(url=_baidu_serp_url(q))
                return q, (r.markdown if isinstance(r.markdown, str)
                           else str(r.markdown)) if getattr(r, "success", False) else ""
            except Exception:  # noqa: BLE001
                return q, ""

        qs = list(dict.fromkeys(q for _, _, q in QUERIES))
        raw = await asyncio.gather(*[one(q) for q in qs])
        serp = {q: md for q, md in raw}
        blocked = [q for q in serp if corpus.serp_looks_blocked(serp[q])]
        print(f"SERP {len(serp)} 查询, 被拦 {len(blocked)} → Bing 兜底")
        if blocked:
            serp.update(await asyncio.to_thread(corpus._bing_serps, blocked))

        seen_global: set[str] = set()
        for cat in dict.fromkeys(c for c, _, _ in QUERIES):
            bdir = ROOT / "data-test" / "corpus" / f"batch-corpus-roster-{cat}-20261030"
            idx_path = bdir / "index.json"
            data = json.loads(idx_path.read_text(encoding="utf-8"))
            seen = {r["url"] for r in data["index"]}
            seen_global |= seen
            got, idx = 0, 200
            for _, st, q in QUERIES:
                if _ != cat or got >= QUOTA_PER_CAT:
                    continue
                for a in corpus.pick_anchors(serp.get(q, ""), 4, seen_global):
                    if got >= QUOTA_PER_CAT:
                        break
                    seen_global.add(a["url"])
                    rec = {"source_type": st, "query": q, "title": a["title"],
                           "url": a["url"], "status": "", "chars": 0, "file": ""}
                    data["index"].append(rec)
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
                    rec["file"] = corpus.write_doc(bdir, idx, rec, body).name
                    rec["status"] = "saved"
                    idx += 1
                    got += 1
            data["plan"]["generic_recrawl"] = "2026-10-30 no-vehicle-filter"
            idx_path.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                                encoding="utf-8")
            print(f"[{cat}] 宏观补爬 {got} 篇")


if __name__ == "__main__":
    asyncio.run(main())
