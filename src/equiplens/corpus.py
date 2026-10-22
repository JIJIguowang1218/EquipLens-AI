"""调研语料采集批（R2 后半前置·第 0 步"先爬后研"）。

目的: 为部件类型学归类与"分析写作规范"提供真实文本语料——设计分析类内容
在网上占比极低, 必须先拿到真实分布再定规范, 不做空想调研。
四类信源配额: official(官网车型页) / spec(参数配置页) / review(媒体评测)
/ industry(行业资讯), 由 plan JSON 给定 queries 与配额。
教训修复: R7 真实抓取只留图不留文——本轮起正文(markdown)一律落盘归档。
纪律: robots 复用 webchannel(B 案)、显式 UA、四类配额帽、页超时、礼貌间隔;
SERP 走 Crawl4AI 真浏览器(roster 实测: requests 直连百度必触发安全验证)。
落盘: data-test/corpus/<batch_id>/NNN-<slug>.md + index.json(规则④⑦)。
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests

from . import webchannel
from .roster import BAIDU_SELF, VEHICLE_WORDS, _baidu_serp_url, _strip_tags

SOURCE_TYPES = ["official", "spec", "review", "industry"]
DEFAULT_QUOTA = {"official": 3, "spec": 2, "review": 4, "industry": 3}
# SERP 锚点过滤: baidu 自有域(roster 教训)、验证页/站内搜索/视频/PDF/收藏评论等功能页
BLOCK_URL_RE = re.compile(
    r"captcha|/s\?|wappass|video|\.pdf($|\?)|tieba|zhidao|wenku"
    r"|/fav|/collect|/comment|/share|/login|/download|/pic|/photo|/album", re.I)
MIN_CHARS = 200  # 正文过短 = 空壳页(登录墙/JS 骨架), 只记索引不落盘


def build_plan(queries: dict[str, list[str]], quota: dict | None = None,
               batch_id: str | None = None) -> dict:
    """校验并补全采集计划: queries 按四类信源分组, 配额默认 DEFAULT_QUOTA。"""
    unknown = set(queries) - set(SOURCE_TYPES)
    if unknown:
        raise ValueError(f"未知信源类型: {sorted(unknown)}, 允许: {SOURCE_TYPES}")
    q = dict(DEFAULT_QUOTA)
    q.update(quota or {})
    return {"batch_id": batch_id or
            f"batch-corpus-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "quota": {k: q[k] for k in SOURCE_TYPES if k in queries},
            "queries": {k: queries[k] for k in SOURCE_TYPES if queries.get(k)}}


def slugify(title: str, url: str) -> str:
    """标题取安全字符做文件名; 无可用字符则退回 URL 哈希。"""
    safe = re.sub(r"[^\w\u4e00-\u9fff]+", "", title)[:16]
    if len(safe) < 4:
        import hashlib
        safe = hashlib.sha1(url.encode()).hexdigest()[:12]
    return safe


def pick_anchors(md: str, max_n: int, exclude: set[str] | None = None) -> list[dict]:
    """SERP markdown → 候选文章链接(title+url)。

    过滤: baidu 自有域与 BLOCK_URL_RE、空/超短标题、已见 URL(exclude); 保序去重。
    """
    out: list[dict] = []
    seen = set(exclude or set())
    if max_n <= 0:
        return out
    for m in re.finditer(r"\[([^\]]+)\]\((http[^)]+)\)", md):
        title = _strip_tags(m.group(1))
        url = m.group(2).strip()
        if len(title) < 4 or url in seen or BAIDU_SELF.search(url) \
                or BLOCK_URL_RE.search(url):
            continue
        if not any(w in title for w in VEHICLE_WORDS) and not any(
                w in url for w in ("truck", "auto", "car", "360che", "d1cm")):
            continue  # 松相关过滤: SERP 混入的无关站推荐位
        seen.add(url)
        out.append({"title": title[:60], "url": url})
        if len(out) >= max_n:
            break
    return out


def write_doc(outdir: Path, idx: int, doc: dict, body: str) -> Path:
    """单篇语料落盘: front matter(元数据) + markdown 正文。"""
    path = outdir / f"{idx:03d}-{slugify(doc['title'], doc['url'])}.md"
    meta = {k: doc.get(k, "") for k in
            ("url", "source_type", "query", "title", "fetched_at", "robots")}
    meta["chars"] = len(body)
    fm = "\n".join(f"{k}: {v}" for k, v in meta.items())
    path.write_text(f"---\n{fm}\n---\n\n{body}\n", encoding="utf-8")
    return path


def summarize(index: list[dict]) -> dict:
    """按信源类型结算: saved / too_short / robots_denied / fetch 失败。"""
    out: dict = {"total": len(index)}
    for st in SOURCE_TYPES:
        rows = [r for r in index if r["source_type"] == st]
        out[st] = {"saved": sum(1 for r in rows if r["status"] == "saved"),
                   "failed": sum(1 for r in rows if r["status"] != "saved")}
    return out


def resolve_redirect(url: str) -> str:
    """百度 /link 跳转 → 真实 URL（robots 检查与溯源都以真实域名为准——
    首轮教训: SERP 锚点全是 baidu/link, 对跳转 URL 做 robots 检查 17/17 全拒）。"""
    if "baidu.com/link" not in url:
        return url
    try:
        r = requests.get(url, headers={"User-Agent": webchannel.UA},
                         timeout=10, stream=True, allow_redirects=True)
        real = r.url
        r.close()
        return real
    except requests.RequestException:
        return url


def collect_corpus(plan: dict, data_dir: Path) -> dict:
    """执行采集批: SERP(并行) → 按类型顺序抓正文(配额帽+robots+间隔)。

    返回 report: {batch_id, outdir, index, summary}; 正文文件 + index.json 落盘。
    """
    plan = build_plan(**{k: plan[k] for k in ("queries", "quota", "batch_id")
                         if k in plan})
    outdir = Path(data_dir) / "corpus" / plan["batch_id"]
    outdir.mkdir(parents=True, exist_ok=True)
    all_queries = [(st, q) for st, qs in plan["queries"].items() for q in qs]
    index: list[dict] = []
    seen: set[str] = set()
    fetched_total = sum(plan["quota"].values())

    async def _run() -> None:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler(headless=True, verbose=False) as c:
            serp_raw = await asyncio.gather(
                *[c.arun(url=_baidu_serp_url(q)) for _, q in all_queries],
                return_exceptions=True)
            serp_md: dict[str, str] = {}
            for (st, q), r in zip(all_queries, serp_raw):
                if hasattr(r, "success") and r.success:
                    serp_md[q] = r.markdown if isinstance(r.markdown, str) \
                        else str(r.markdown)
            idx = 1
            for st in SOURCE_TYPES:
                if st not in plan["queries"]:
                    continue
                quota, got = plan["quota"][st], 0
                for st_, q in all_queries:
                    if st_ != st or got >= quota:
                        continue
                    for a in pick_anchors(serp_md.get(q, ""), quota - got, seen):
                        seen.add(a["url"])
                        real = resolve_redirect(a["url"])
                        rec = {"source_type": st, "query": q,
                               "title": a["title"], "url": real,
                               "status": "", "chars": 0, "file": ""}
                        index.append(rec)
                        if real != a["url"] and BLOCK_URL_RE.search(real):
                            rec["status"] = "blocked_url"  # 解析后落入功能页(收藏/图库等)
                            continue
                        if not webchannel.robots_allows(real):
                            rec["status"] = "robots_denied"
                            continue
                        time.sleep(webchannel.SLEEP_SECONDS)
                        try:
                            r = await c.arun(url=real)
                        except Exception as e:  # noqa: BLE001
                            rec["status"] = f"fetch_error: {type(e).__name__}"
                            continue
                        if not (hasattr(r, "success") and r.success):
                            rec["status"] = "fetch_failed"
                            continue
                        body = r.markdown if isinstance(r.markdown, str) \
                            else str(r.markdown)
                        meta_title = ""
                        md_meta = getattr(r, "metadata", None)
                        if isinstance(md_meta, dict):
                            meta_title = str(md_meta.get("title") or "")
                        rec["title"] = (meta_title.strip() or a["title"])[:60]
                        rec["chars"] = len(body)
                        if len(body) < MIN_CHARS:
                            rec["status"] = "too_short"
                            continue
                        rec["robots"] = "allow"
                        rec["fetched_at"] = datetime.now().isoformat(timespec="seconds")
                        rec["file"] = write_doc(outdir, idx, rec, body).name
                        rec["status"] = "saved"
                        idx += 1
                        got += 1
                        if got >= quota or idx > fetched_total:
                            break

    asyncio.run(_run())
    (outdir / "index.json").write_text(
        json.dumps({"batch_id": plan["batch_id"], "plan": plan, "index": index},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    return {"batch_id": plan["batch_id"], "outdir": str(outdir),
            "index": index, "summary": summarize(index)}
