# -*- coding: utf-8 -*-
"""T18-roster：全名录大规模文本爬取批（4 类目 39 车型）。

设计要点：
- 车型清单 = T13-T15 锁定的 4 份 roster-search-report 的 reports.vehicle；
- 每车型 2 查询（review/industry 各一）+ 类目级 design_media/academic 查询
  （专捕"不指向车型的宏观设计分析"）；
- 轮转取锚：每查询最多取 3 锚点后按列轮转，避免先到查询吃满配额
  （corpus.collect_corpus 顺序取锚有偏，本轮改用轮转，公平覆盖各车型）；
- SERP 走 Crawl4AI 真浏览器（baidu），被拦查询自动落 Bing RSS；
- robots/礼貌间隔/UA/落盘格式复用 corpus 与 webchannel 的既有纪律；
- skip_domains 沿用 T18 教训（爱采购/豆丁/百科）。

用法: PYTHONPATH=src python tmp/run_roster_crawl.py
输出: data-test/corpus/batch-corpus-roster-<cat>-20261030/
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
DATA_DIR = ROOT / "data-test"
SKIP_DOMAINS = ["docin.com", "baike.baidu.com", "b2b.baidu.com"]

# T13-T15 锁定名录（vehicle 字段原样）
ROSTERS: dict[str, list[str]] = {
    "沙漠牵引车": ["陕汽重卡德龙6X6", "陕汽重卡德龙", "陕汽重卡德龙F3000",
                   "东风天锦", "陕汽重卡德龙X3000", "一汽解放JH6",
                   "中国重汽ZZ425", "中国重汽汕德卡C7H", "中国重汽HOWO",
                   "中国重汽MAX", "东风龙H5", "一汽解放J6G"],
    "重型吊车": ["徐工XGC88000", "三一SAC16000S", "中联重科ZTC250", "徐工QY35K5",
                 "徐工QY25K5C", "徐工XCT25", "中联重科QAY25", "三一STC500",
                 "福田BJ5311JSQ"],
    "轻型吊车": ["徐工QY25K5C", "徐工XCT8L4", "雷萨FTC25X5", "三一STC800C6",
                 "雷萨FTC55X5", "徐工QY16KC", "三一QY25C", "三一STC550C5",
                 "三一STC1300C8", "徐工QY25K5F", "中联重科ZTC250A"],
    "翻斗铲车": ["福田金刚", "福田金刚3", "福田金刚C", "沃尔沃FMX",
                 "一汽解放J6L", "陕汽重卡德龙K3000", "陕汽重卡德龙X5000E"],
}

# 类目级查询：主捕"非指向"宏观设计分析（报告第③类）
CATEGORY_QUERIES: dict[str, list[str]] = {
    "沙漠牵引车": ["沙漠牵引车 造型 设计", "油田牵引车 外观 设计",
                   "重型卡车 家族化 设计语言", "工程机械 工业设计 趋势"],
    "重型吊车": ["汽车起重机 造型 设计", "起重机 外观 设计语言",
                 "履带吊 造型设计", "工程机械 工业设计 趋势"],
    "轻型吊车": ["随车吊 造型 设计", "小型起重机 外观 设计",
                 "汽车起重机 驾驶室 设计", "工程机械 工业设计 趋势"],
    "翻斗铲车": ["自卸车 造型 设计", "矿用卡车 外观 设计",
                 "自卸车 货厢 设计", "工程机械 工业设计 趋势"],
}

QUOTA = {"review": 12, "industry": 8, "design_media": 4, "official": 2,
         "academic": 2}
PER_QUERY_ANCHORS = 3  # 每查询先截 3 锚，再轮转


def build_queries(cat: str, vehicles: list[str]) -> dict[str, list[str]]:
    return {
        "review": [f"{v} 外观 评测 设计" for v in vehicles],
        "industry": [f"{v} 造型 设计语言" for v in vehicles],
        "design_media": CATEGORY_QUERIES[cat][:2],
        "official": [f"{vehicles[0]} 官方网站", f"{vehicles[-1]} 官方网站"],
        "academic": [CATEGORY_QUERIES[cat][2], CATEGORY_QUERIES[cat][3]],
    }


def interleave(per_query: dict[str, list[dict]]) -> list[dict]:
    """按列轮转合并各查询锚点，保证车型公平覆盖。"""
    cols = [anchors[:PER_QUERY_ANCHORS] for anchors in per_query.values()
            if anchors]
    out: list[dict] = []
    for i in range(max((len(c) for c in cols), default=0)):
        for col in cols:
            if i < len(col):
                out.append(col[i])
    return out


async def crawl_category(cat: str, vehicles: list[str],
                         browser: AsyncWebCrawler) -> dict:
    batch_id = f"batch-corpus-roster-{cat}-20261030"
    queries = build_queries(cat, vehicles)
    all_qlist = [(st, q) for st, qs in queries.items() for q in qs]
    print(f"[{cat}] SERP {len(all_qlist)} 查询 ...", flush=True)

    serp_md: dict[str, str] = {}
    raw = await asyncio.gather(
        *[_fetch_serp(browser, q) for _, q in all_qlist],
        return_exceptions=True)
    for (_, q), r in zip(all_qlist, raw):
        if isinstance(r, str) and r:
            serp_md[q] = r
    blocked = [q for q in serp_md if corpus.serp_looks_blocked(serp_md[q])]
    if blocked:
        print(f"[{cat}] {len(blocked)} 查询被拦 → Bing RSS 兜底", flush=True)
        serp_md.update(await asyncio.to_thread(corpus._bing_serps, blocked))

    outdir = DATA_DIR / "corpus" / batch_id
    outdir.mkdir(parents=True, exist_ok=True)
    index: list[dict] = []
    seen: set[str] = set()
    idx = 1
    for st in corpus.SOURCE_TYPES:
        quota, got = QUOTA.get(st, 0), 0
        if st not in queries:
            continue
        anchors_by_q = {
            q: corpus.pick_anchors(serp_md.get(q, ""), PER_QUERY_ANCHORS,
                                   seen, relevant_terms=vehicles + [cat])
            for st_, q in all_qlist if st_ == st}
        for a in interleave(anchors_by_q):
            if got >= quota:
                break
            seen.add(a["url"])
            rec = {"source_type": st, "query": "", "title": a["title"],
                   "url": a["url"], "status": "", "chars": 0, "file": ""}
            index.append(rec)
            real = corpus.resolve_redirect(a["url"])
            rec["url"] = real
            host = (urlparse(real).hostname or "").lower()
            if any(host == d or host.endswith("." + d)
                   for d in SKIP_DOMAINS):
                rec["status"] = "source_skipped"
                continue
            if not webchannel.robots_allows(real):
                rec["status"] = "robots_denied"
                continue
            time.sleep(webchannel.SLEEP_SECONDS)
            try:
                r = await browser.arun(url=real)
            except Exception as e:  # noqa: BLE001
                rec["status"] = f"fetch_error: {type(e).__name__}"
                continue
            if not (hasattr(r, "success") and r.success):
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
            rec["file"] = corpus.write_doc(outdir, idx, rec, body).name
            rec["status"] = "saved"
            idx += 1
            got += 1

    plan = {"batch_id": batch_id, "category": cat, "vehicles": vehicles,
            "quota": QUOTA, "queries": queries,
            "skip_domains": SKIP_DOMAINS, "serp_channel": "baidu+bing-fallback",
            "interleave": f"per_query={PER_QUERY_ANCHORS}"}
    (outdir / "index.json").write_text(
        json.dumps({"batch_id": batch_id, "plan": plan, "index": index},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    saved = sum(1 for r in index if r["status"] == "saved")
    print(f"[{cat}] 完成: {saved}/{len(index)} 落盘 → {outdir}", flush=True)
    return {"batch_id": batch_id, "total": len(index), "saved": saved}


async def _fetch_serp(browser: AsyncWebCrawler, q: str) -> str:
    try:
        r = await browser.arun(url=_baidu_serp_url(q))
    except Exception:  # noqa: BLE001
        return ""
    if hasattr(r, "success") and r.success:
        return r.markdown if isinstance(r.markdown, str) else str(r.markdown)
    return ""


async def main() -> None:
    results = []
    async with AsyncWebCrawler(headless=True, verbose=False) as browser:
        for cat, vehicles in ROSTERS.items():
            results.append(await crawl_category(cat, vehicles, browser))
    (DATA_DIR / "corpus" / "roster-crawl-summary-20261030.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ALL DONE:", results, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
