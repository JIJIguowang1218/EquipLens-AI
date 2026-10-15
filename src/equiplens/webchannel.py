"""真实渠道（合规 B 案：厂商官网受控抓取）。

纪律: robots.txt 检查（无 robots 视为允许）、显式 UA、预算帽（页数/每页图数/总量）、
礼貌间隔、来源 URL 全留痕、授权默认 web_third_party 待确认。
渲染: 厂商官网多为 JS 门户，经 Crawl4AI（playwright）渲染后用与夹具相同的 PageParser 抽取。
"""

from __future__ import annotations

import re
import time
import urllib.robotparser
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import requests

from . import ingest
from .channels import ExtractedPage, PageParser, map_alt_to_tags

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) EquipLensResearch/0.1 "
      "(internal product-analysis crawler; no AI training)")
MAX_IMG_BYTES = 8 * 1024 * 1024
MIN_IMG_WIDTH = 350
SKIP_IMG_RE = re.compile(r"\.(svg|gif|ico)(\?|$)|logo|icon|banner|weibo|wechat|qr|二维码|扫码|布局|地图", re.I)
URL_BLOCK_RE = re.compile(r"qr|二维码|erweima|扫码|weixin|wechat|weibo|布局|地图|/map|about|contact"
                          r"|zhaopin|job|recruit|login|register|xinyong|copyright|friendlink", re.I)
SLEEP_SECONDS = 1.2

_robots_cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}


def robots_allows(url: str) -> bool:
    """robots.txt 检查（B 案纪律）。拉取失败视为允许；命中 Disallow 则弃用该 URL。"""
    m = re.match(r"(https?://[^/]+)", url)
    if not m:
        return False
    host = m.group(1)
    if host not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = requests.get(host + "/robots.txt", headers={"User-Agent": UA}, timeout=8)
            rp.parse(r.text.splitlines() if r.status_code == 200 else [])
        except requests.RequestException:
            rp.parse([])
        _robots_cache[host] = rp
    rp = _robots_cache[host]
    return rp.can_fetch(UA, url) if rp else True


def _render_pages(urls: list[str]) -> dict[str, str]:
    """Crawl4AI 渲染 JS 门户页 → url: 渲染后 HTML。"""
    import asyncio
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    async def _run() -> dict[str, str]:
        out = {}
        async with AsyncWebCrawler(config=BrowserConfig(headless=True, user_agent=UA)) as crawler:
            results = await crawler.arun_many(
                urls, config=CrawlerRunConfig(page_timeout=35000, verbose=False))
            for r in results:
                if r.success and r.html:
                    out[r.url] = r.html
        return out

    return asyncio.run(_run())


@dataclass
class WebPage:
    url: str
    page: ExtractedPage


class WebChannel:
    """厂商官网渠道：持有已渲染页面，提供与夹具一致的图片字节读取。"""

    name = "厂商官网渠道(B案受控抓取)"

    def __init__(self, rendered: dict[str, str]):
        self.hits: list[WebPage] = []
        for url, html_text in rendered.items():
            parser = PageParser()
            try:
                parser.feed(html_text)
            except Exception:
                continue
            base = re.match(r"(https?://[^/]+)", url)
            abs_imgs = []
            for i in parser.images:
                src = i.src.strip()
                if not src or src.startswith("data:"):
                    continue
                if src.startswith("//"):
                    src = (base.group(1).split(":")[0] if base else "https") + ":" + src
                elif not src.startswith("http") and base:
                    src = base.group(1) + src
                abs_imgs.append(type(i)(src=src, alt=i.alt))
            imgs = [i for i in abs_imgs
                    if i.src.startswith("http") and not SKIP_IMG_RE.search(i.src)]
            if imgs:
                page = ExtractedPage(path=Path(url), title=parser.title.strip(),
                                     h1=parser.h1.strip(), images=imgs,
                                     params=parser.params)
                self.hits.append(WebPage(url=url, page=page))

    def find_pages(self, keyword: str | None = None) -> list[WebPage]:
        if not keyword:
            return self.hits
        return [h for h in self.hits
                if keyword in h.page.title or keyword in h.page.h1
                or any(keyword in (i.alt or "") for i in h.page.images)]

    def read_bytes(self, src: str) -> bytes:
        from urllib.parse import quote
        safe_src = quote(src, safe=":/?&=%._-#")  # 中文文件名 URL 编码（latin-1 缺陷修复）
        r = requests.get(safe_src, headers={"User-Agent": UA, "Referer": src}, timeout=25, stream=True)
        r.raise_for_status()
        if not r.headers.get("content-type", "").startswith("image"):
            raise ValueError(f"非图片 content-type: {r.headers.get('content-type')}")
        data = b""
        for chunk in r.iter_content(65536):
            data += chunk
            if len(data) > MAX_IMG_BYTES:
                raise ValueError("图片超过 8MB 上限")
        return data


def _same_domain(url: str, root: str) -> bool:
    return re.match(r"(https?://[^/]+)", url).group(1) == re.match(r"(https?://[^/]+)", root).group(1)


def discover_product_urls(rendered_home: dict[str, str], roots: list[str],
                          keywords: list[str], max_links: int) -> list[str]:
    """渲染后的首页 → 同域链接，按关键词命中（锚文本或 href）筛选产品页。"""
    found: list[str] = []
    seen = set()
    for root in roots:
        home_html = next((h for u, h in rendered_home.items() if _same_domain(u, root)), "")
        if not home_html:
            continue
        for m in re.finditer(r'<a[^>]+href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', home_html,
                             re.I | re.S):
            href, anchor = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if href.startswith(("#", "javascript")):
                continue
            if href.startswith("/"):
                href = re.match(r"(https?://[^/]+)", root).group(1) + href
            if not href.startswith("http") or not _same_domain(href, root):
                continue
            if URL_BLOCK_RE.search(href) or URL_BLOCK_RE.search(anchor):
                continue
            blob = href + " " + anchor
            if any(k in blob for k in keywords) and href not in seen:
                seen.add(href)
                found.append(href)
    return found[:max_links]


def discover_from_pages(rendered: dict[str, str], roots: list[str],
                        keywords: list[str], max_links: int, exclude: set) -> list[str]:
    """第二波发现：从产品列表页里挖车型详情页。"""
    out: list[str] = []
    seen = set(exclude)
    for url, html_text in rendered.items():
        for m in re.finditer(r'<a[^>]+href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', html_text,
                             re.I | re.S):
            href, anchor = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if href.startswith(("#", "javascript")):
                continue
            if href.startswith("/"):
                href = re.match(r"(https?://[^/]+)", url).group(1) + href
            if not href.startswith("http") or not any(_same_domain(href, r) for r in roots):
                continue
            if href in seen or URL_BLOCK_RE.search(href) or URL_BLOCK_RE.search(anchor):
                continue
            blob = href + " " + anchor
            if any(k in blob for k in keywords):
                seen.add(href)
                out.append(href)
            if len(out) >= max_links:
                return out
    return out


def crawl_vendor_sites(conn, data_dir: Path, roots: list[str], *,
                       keywords: list[str] | None = None,
                       max_pages: int = 10, images_per_page: int = 10,
                       max_total: int = 40, license: str = "web_third_party") -> dict:
    """B 案真实抓取入口：渲染首页 → 发现产品页 → 渲染产品页 → 图片候选入库。

    预算三帽: max_pages / images_per_page / max_total。返回 batch 报告。
    """
    keywords = keywords or ["牵引", "重卡", "卡车", "产品"]
    batch_id = f"batch-web-{uuid.uuid4().hex[:10]}"
    report = {"batch_id": batch_id, "roots": roots, "pages_crawled": 0,
              "candidates": 0, "skipped": 0, "denied_robots": 0, "pages": []}

    root_set = {r.rstrip("/") for r in roots}
    home = {u: h for u, h in _render_pages(roots).items()}
    # 两波发现: 首页→产品列表页→车型详情页（首页自身不作图片来源——首轮教训: 轮播/杂图主因）
    listing_urls = discover_product_urls(home, roots, keywords, max_pages)
    listing = _render_pages(listing_urls) if listing_urls else {}
    detail_urls = discover_from_pages(listing, roots,
                                      ["车型", "详情", "配置", "参数"] + keywords,
                                      max_pages, exclude=set(listing_urls) | root_set)
    detail = _render_pages(detail_urls[:max_pages]) if detail_urls else {}

    rendered = {}
    for src_dict in (listing, detail):
        rendered.update(src_dict)
    channel = WebChannel(rendered)

    for hit in channel.hits:
        if hit.url.rstrip("/") in root_set:
            continue  # 首页不当图片来源（第二轮策略）
        if report["candidates"] >= max_total:
            report["pages"].append({"url": hit.url, "note": "达到总量帽，截断"})
            break
        if not robots_allows(hit.url):
            report["denied_robots"] += 1
            continue
        page_report = {"url": hit.url, "title": hit.page.title[:60], "images": []}
        taken = 0
        for img in hit.page.images:
            if taken >= images_per_page or report["candidates"] >= max_total:
                break
            time.sleep(SLEEP_SECONDS)
            try:
                data = channel.read_bytes(img.src)
                from PIL import Image
                from io import BytesIO
                probe = Image.open(BytesIO(data))
                if probe.size[0] < MIN_IMG_WIDTH:
                    raise ValueError(f"图片过小 {probe.size}")
                view, part = map_alt_to_tags(img.alt or "", conn)
                result = ingest.ingest_file_bytes(
                    conn, data_dir, name=Path(img.src).name, data=data,
                    platform=channel.name, license=license, batch_id=batch_id,
                    view_angle=view, part_id=part,
                    evidence_note=f"alt: {img.alt or '(无 alt)'}｜页标题: {hit.page.title or '(无)'}｜URL: {hit.url}",
                    source_url=hit.url)
            except Exception as e:  # noqa: BLE001
                report["skipped"] += 1
                page_report["images"].append({"src": img.src[:90], "status": f"跳过: {e}"})
                continue
            taken += 1
            report["candidates"] += 1
            page_report["images"].append({"src": img.src[:90], "status": result["status"],
                                          "asset_id": result["asset_id"]})
        report["pages_crawled"] += 1
        report["pages"].append(page_report)
    return report
