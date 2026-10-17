"""R2 首半：名录生成器（意见 #14——产品负责人只给类目, EL 检索生成候选名录）。

来源链（意见 #3 用户工作流同构）: 百度网页搜索"类目+车型榜单"文章 → 结果块
（标题+摘要）内做品牌×型号抽取 → 跨查询频次合并 → 候选名录。
技术要点（2026-10-17 实测）: 百度网页搜索 requests 直连必触发安全验证,
Bing 网页搜索被反爬降级——SERP 与重定向解析一律走 Crawl4AI 真浏览器渲染;
百度自家域名（图片/智能小程序/精选笔记）与验证页不作文章源。
名录是"锁定的闭集"的前身：产出候选 → 产品负责人增删锁定 → 才进搜图（imagesearch）。
呈现层中文, 名录 JSON 归档 data-test/（规则④）。
"""

from __future__ import annotations

import html
import json
import re
import urllib.parse
from datetime import datetime
from pathlib import Path

# 品牌词典（工程机械+重卡, 含常见子品牌别称; 抽取与归一用）
BRANDS: dict[str, str] = {
    "解放": "一汽解放", "一汽解放": "一汽解放",
    "东风": "东风", "陕汽": "陕汽重卡", "陕汽重卡": "陕汽重卡",
    "重汽": "中国重汽", "中国重汽": "中国重汽", "豪沃": "中国重汽",
    "HOWO": "中国重汽", "汕德卡": "中国重汽",
    "福田": "福田", "欧曼": "福田欧曼", "欧航": "福田",
    "江淮": "江淮", "格尔发": "江淮", "江铃": "江铃",
    "红岩": "上汽红岩", "杰狮": "上汽红岩", "杰卡": "上汽红岩",
    "大运": "大运", "北奔": "北奔", "北方奔驰": "北奔",
    "联合重卡": "联合重卡", "三一": "三一", "徐工": "徐工",
    "中联": "中联重科", "中联重科": "中联重科", "柳工": "柳工",
    "龙工": "龙工", "临工": "山东临工", "厦工": "厦工",
    "山推": "山推", "同力": "同力重工", "北方股份": "北方股份",
    "宇通": "宇通重工", "太脱拉": "太脱拉", "TATRA": "太脱拉",
    "卡特彼勒": "卡特彼勒", "Caterpillar": "卡特彼勒", "小松": "小松",
    "沃尔沃": "沃尔沃", "奔驰": "奔驰", "斯堪尼亚": "斯堪尼亚",
    "曼恩": "曼恩", "MAN": "曼恩", "达夫": "达夫", "依维柯": "依维柯",
    "雷萨": "雷萨",
}
_BRAND_ALT = sorted(BRANDS, key=len, reverse=True)
# 型号 token: 字母数字型号（X3000/NG80/V3/JH6/CT250/工厂码 ZZ4257V3247B1）
# 或中文系列名（可带数字/驱动形式后缀, 如 德龙6X6）
_MODEL_TOKEN = re.compile(
    r"[A-Z]{1,4}[0-9A-Z]{2,14}"
    r"|(?:德龙|豪沃|杰狮|金刚|天锦|天龙|汕德卡|欧曼|格尔发|杰卡|星光|王牌|汉风|龙V|龙H)"
    r"[A-Za-z0-9xX×]{0,6}")
_NOISE = re.compile(r"^[0-9]{1,4}$|马力|轴距|驱动|国六|排放|报价|价格|参数|图片|官网")
VEHICLE_WORDS = ["卡车", "重卡", "牵引", "吊车", "起重机", "装载机", "铲车",
                 "自卸", "工程车", "矿卡", "车型", "商用车", "油田", "运输",
                 "越野", " delivery".strip()]
BLOCK_RE = re.compile(r'<h3[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S)
BAIDU_SELF = re.compile(
    r"wappass\.baidu\.com|/captcha|image\.baidu\.com|smartapps\.baidu\.com"
    r"|baidu\.com/s\?|tieba\.baidu\.com|zhidao\.baidu\.com|wenku\.baidu\.com"
    r"|map\.baidu\.com|baike\.baidu\.com")


def _relevant(category: str, title: str) -> bool:
    """标题相关性: 类目词命中或含任一车辆词（地理/百科科普直接丢弃）。"""
    return category in title or any(w in title for w in VEHICLE_WORDS)


def _strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def extract_models(text: str) -> list[tuple[str, str]]:
    """品牌 × 型号 抽取: 找品牌词位置, 向后看 12 字符内抓型号 token。"""
    out = []
    for m in re.finditer("|".join(re.escape(b) for b in _BRAND_ALT), text):
        brand = BRANDS[m.group(0)]
        t = _MODEL_TOKEN.search(text[m.end():m.end() + 12])
        if t:
            model = t.group(0).strip("-—·× ")
            if not _NOISE.search(model):
                out.append((brand, model.upper()))
    return out


def _baidu_serp_url(query: str) -> str:
    return "https://www.baidu.com/s?wd=" + urllib.parse.quote(query) + "&rn=10"


async def _crawl_serp(queries: list[str]) -> dict:
    from crawl4ai import AsyncWebCrawler
    async with AsyncWebCrawler(headless=True, verbose=False) as c:
        return {q: await c.arun(url=_baidu_serp_url(q)) for q in queries}


def _scan_lines(md: str, q: str, src: dict | None, category: str,
                state: dict) -> None:
    """markdown 按行扫描: 标题锚点记来源/来源文章, 正文行抽品牌×型号。"""
    counter, articles, article_links = (state["counter"], state["articles"],
                                        state["article_links"])
    cur_src = src
    for line in md.splitlines():
        line = line.strip()
        if not line:
            continue
        anchor = re.search(r"\[([^\]]+)\]\((http[^)]+)\)", line)
        if line.lstrip().startswith("#") and anchor:
            cand = {"title": _strip_tags(anchor.group(1))[:60],
                    "url": anchor.group(2), "query": q}
            if _relevant(category, cand["title"]):
                articles.append(cand)
                if not BAIDU_SELF.search(cand["url"]) and \
                        cand["url"] not in {a["url"] for a in article_links}:
                    article_links.append(cand)
                cur_src = cand
            continue
        for brand, model in extract_models(line):
            key = (brand, model)
            rec = counter.setdefault(
                key, {"brand": brand, "model": model, "mentions": 0,
                      "sources": []})
            rec["mentions"] += 1
            if cur_src and cur_src["title"] not in \
                    [s["title"] for s in rec["sources"]] and len(rec["sources"]) < 3:
                rec["sources"].append(cur_src)


def generate_roster(category: str, data_dir: Path, max_articles: int = 8,
                    top_n: int = 12) -> dict:
    """类目 → 候选名录。两阶段共用一次浏览器会话:
    ①SERP markdown 扫描 → 候选+来源文章链接 ②抓来源正文页再扫一轮增厚。
    技术要点（2026-10-17 实测）: 百度网页搜索 requests 直连必触发安全验证,
    Bing 网页搜索被反爬降级——全部走 Crawl4AI 真浏览器渲染。"""
    import asyncio

    queries = [f'"{category}" 车型大全 推荐', f'"{category}" 有哪些型号',
               f'{category} 6x6 油田', f'"{category}" 品牌 报价',
               f'{category} 越野 卡车 型号']
    state = {"counter": {}, "articles": [], "article_links": []}

    async def _crawl():
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler(headless=True, verbose=False) as c:
            # 并行抓 SERP（此前串行——产品负责人反馈"生成名录太慢"）
            serp_raw = await asyncio.gather(
                *[c.arun(url=_baidu_serp_url(q)) for q in queries],
                return_exceptions=True)
            pages = {q: r for q, r in zip(queries, serp_raw)
                     if hasattr(r, "success") and r.success}
            for q in queries:
                page = pages.get(q)
                if page is None:
                    continue
                md = page.markdown if isinstance(page.markdown, str) \
                    else str(page.markdown)
                _scan_lines(md, q, None, category, state)
            arts_raw = await asyncio.gather(
                *[c.arun(url=a["url"]) for a in state["article_links"][:max_articles]],
                return_exceptions=True)
            art_pages = {a["url"]: r for a, r in zip(
                state["article_links"][:max_articles], arts_raw)
                if hasattr(r, "success") and r.success}
            return pages, art_pages

    try:
        _, art_pages = asyncio.run(_crawl())
    except Exception:  # noqa: BLE001
        art_pages = {}
    for url, page in art_pages.items():
        if page is None or not page.success:
            continue
        src = next((a for a in state["article_links"] if a["url"] == url), None)
        md = page.markdown if isinstance(page.markdown, str) else str(page.markdown)
        _scan_lines(md, src["query"] if src else "", src, category, state)

    roster = sorted(state["counter"].values(),
                    key=lambda r: -r["mentions"])[:top_n]
    out = {"category": category,
           "generated_at": datetime.now().isoformat(timespec="seconds"),
           "status": "pending_lock",
           "queries": queries,
           "articles": state["articles"],
           "candidates": roster}
    data_dir = Path(data_dir)
    path = data_dir / f"roster-{category}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    out["path"] = str(path)
    return out
