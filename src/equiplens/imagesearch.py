"""搜索渠道（Bing 中国图片搜索端点）：对齐产品负责人"百度图片"人肉检索工作流。

按"品牌+型号"查询词搜图 → 候选图下载 → 门卫过滤 → 入库。
证据等级: 搜索词声称型号 = co_occurrence_only(弱关联 T3)，provisional 挂载待人工确认——
搜索结果可能错配(B1)，不给强证据。
合规: 搜索端点抓取处于灰色地带(B 案"API 优先"的例外)，已明示 UA、限速、
授权默认 web_third_party、来源记录查询词与结果页。
"""

from __future__ import annotations

import json
import re
import time
from html.parser import HTMLParser
import uuid
from pathlib import Path
from urllib.parse import quote

import requests

from . import gate, ingest

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) EquipLensResearch/0.1 "
      "(internal product-analysis crawler; no AI training)")
SLEEP_SECONDS = 1.0
MAX_IMG_BYTES = 8 * 1024 * 1024
MIN_IMG_WIDTH = 350
# 图片 CDN 常按 Referer 放行；用搜索页当 Referer，而不是图片自身 URL。
CHANNEL_REFERERS = {
    "360": "https://image.so.com/",
    "baidu": "https://image.baidu.com/",
    "bing": "https://cn.bing.com/images/",
}
SKIP_IMG_RE = re.compile(r"\.(svg|gif|ico)(\?|$)|logo|icon|banner|qrcode", re.I)


def search_images(query: str, limit: int = 12) -> list[dict]:
    """按型号搜图：多通道 + 健康检查 + 相关性护栏。

    通道顺序：360 图片 → 百度 → Bing。每个通道返回后先过"相关性护栏"
    （标题须含查询短语或其任一 token），不相关则记 `unrelated` 并换下一个通道；
    被反爬/验证页拦截记 `blocked`。全部失败返回空，由调用方如实上报，不拿垃圾充数。
    """
    hits, _ = search_images_ex(query, limit)
    return hits


def search_model_images(model: str, limit: int = 12, *,
                        hd: bool = False) -> tuple[list[dict], list[dict]]:
    """按型号取图：基础阶梯；hd=True 时加“高清/大图”段并优先高清。"""
    queries = [f"{model} 工程车", model]
    if hd:
        queries += [f"{model} 高清", f"{model} 大图"]
    return _search_many(queries, limit, model=model)


def search_images_ex(query: str, limit: int = 12,
                     model: str | None = None) -> tuple[list[dict], list[dict]]:
    """返回 (hits, channel_diag)。hits 里带 `channel` 字段。"""
    diag: list[dict] = []
    collected: list[dict] = []
    seen: set[str] = set()
    for name, fn in (("360", _search_360), ("baidu", _search_baidu),
                     ("bing", _search_bing)):
        try:
            got, status = fn(query, max(limit, 12))
        except Exception as e:  # noqa: BLE001
            got, status = [], f"error:{type(e).__name__}"
        rel = [h for h in got if _relevant(query, h.get("title", ""), model)]
        diag.append({"channel": name, "returned": len(got),
                     "relevant": len(rel), "status": status})
        for h in rel:  # 多通道累加 + 去重，稀疏查询也不至于颗粒无收
            if h["url"] in seen:
                continue
            seen.add(h["url"])
            h["channel"] = name
            collected.append(h)
            if len(collected) >= limit:
                return collected[:limit], diag
    return collected[:limit], diag


def _search_many(queries: list[str], limit: int, *,
                 model: str | None = None,
                 harvest: int = 0) -> tuple[list[dict], list[dict]]:
    """多段查询合并：去重、记录每段诊断、高分辨率优先返回。

    `harvest=N`：取前 N 个来源页（360 结果里的 `link`）回访，抽整页图片。
    实测一篇文章页 30 张图、7/8 能升到 1200×800，远高于“每查询 1.8 张可用”。
    """
    seen: set[str] = set()
    out: list[dict] = []
    diag: list[dict] = []
    for q in queries:
        hits, d = search_images_ex(q, limit, model=model)
        diag.append({"query": q, "channels": d})
        for h in hits:
            if h["url"] in seen:
                continue
            seen.add(h["url"])
            out.append(h)
        big = sum(1 for h in out if int(h.get("width") or 0) >= 1200)
        if big >= limit:
            break
    # 先按 limit 截断搜索命中，再挂来源页结果：否则 harvest>0 时搜索侧会多出
    # 未截断的命中，A/B 就不公平（实测会多出 60% 候选）。
    out = out[:limit]
    if harvest:
        pages: list[str] = []
        for h in out:
            su = h.get("source_url") or ""
            if su and su not in pages and page_priority(su) >= 0:
                pages.append(su)
        pages.sort(key=page_priority, reverse=True)
        seen_urls = {h["url"] for h in out}
        harvested = 0
        for su in pages[:harvest]:
            for h in harvest_source_page(su, limit=8):
                if h["url"] in seen_urls:
                    continue
                seen_urls.add(h["url"])
                out.append(h)
                harvested += 1
        diag.append({"query": "__harvest__",
                     "channels": [{"channel": "page", "returned": harvested,
                                   "pages": pages[:harvest],
                                   "status": "ok" if harvested else "empty"}]})
    # 稳定排序：高分辨率在前，组内保持原召回顺序
    out.sort(key=lambda h: int(h.get("width") or 0) >= 1200, reverse=True)
    return out, diag


def search_images_hd(query: str, limit: int = 12, *,
                     model: str | None = None,
                     hd: bool = True,
                     harvest: int = 0) -> tuple[list[dict], list[dict]]:
    """按一个查询取图：原查询 + 高清/大图段；可选回访来源页。"""
    queries = [query]
    if hd:
        queries += [f"{query} 高清", f"{query} 大图"]
    return _search_many(queries, limit, model=model, harvest=harvest)


def _tokens(s: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", str(s).lower())
            if len(t) >= 2]


# 与车无关的高频污染词（实测：解放→解放战争、壁纸/动漫/表情包等）
NON_VEHICLE = ("战争", "壁纸", "动漫", "表情包", "简笔画", "插画", "电影", "电视剧",
               "游戏", "头像", "试卷", "考试", "招生", "招聘", "梗", "铜人", "梅西",
               "模型", "车模", "玩具", "乐高", "合金", "拼装", "1:24", "1:18")
GENERIC = {"6x6", "4x4", "8x8", "6*6", "工程车", "卡车", "货车", "牵引车",
           "自卸车", "专用车", "越野车", "载货车"}
VEHICLE_WORDS = ("卡车", "货车", "牵引", "自卸", "载货", "工程", "吊车", "起重",
                 "专用车", "越野", "底盘", "驾驶室")


CONF_RE = re.compile(r"\d+\s*[x×]\s*\d+", re.I)


def _config_tokens(s: str) -> list[str]:
    """构型词（6x6/8x8/4x2）：标题必须同构型，防"NG80 6x2"冒充 6x6。"""
    return [re.sub(r"[×\s]", "x", m).lower() for m in CONF_RE.findall(s)]


def _distinctive(model: str) -> list[str]:
    """型号里"能唯一定位到这台车"的字母数字串（NG80 / CA2191P2K2T / X3000 / C7H）。"""
    return [t for t in _tokens(model)
            if re.search(r"\d", t) and t not in GENERIC and len(t) >= 3]


def _relevant(query: str, title: str, model: str | None = None) -> bool:
    """相关性护栏（型号优先）：

    1) 标题含"非车污染词"（解放战争/壁纸/动漫…）→ 直接判不相关；
    2) 型号里有字母数字代码（NG80/X3000/C7H…）→ 标题必须含该代码；
    3) 没有代码 → 标题须含品牌词 + 一个车辆词。
    """
    t = (title or "").lower()
    if not t:
        return False
    if any(w in t for w in NON_VEHICLE):
        return False
    src = model or query
    tn = re.sub(r"[×\s]", "x", t)
    for c in _config_tokens(src):  # 构型不一致 → 直接不相关
        if c not in tn:
            return False
    codes = _distinctive(src)
    if codes and all(c in t for c in codes[:2]):
        return True  # 型号代码直接命中：最强
    # 代码没命中时退回"品牌 + 车辆词"（召回优先；身份真伪交给门卫 + 人工）
    toks = _tokens(src)
    brand = next((x for x in toks if not re.search(r"\d", x) and x not in GENERIC), None)
    if brand:
        # 有品牌词就要求品牌出现；仅凭"工程车/卡车"这类泛词不算命中
        return brand in t and any(w in t for w in VEHICLE_WORDS)
    return any(w in t for w in VEHICLE_WORDS)


def _search_360(query: str, limit: int) -> tuple[list[dict], str]:
    """360 图片（image.so.com）——本环境实测唯一返回相关结果的通道。"""
    try:
        r = requests.get("https://image.so.com/j",
                         params={"q": query, "src": "srp", "sn": 0, "pn": max(30, limit)},
                         headers={"User-Agent": UA, "Referer": "https://image.so.com/"},
                         timeout=20)
    except Exception as e:  # noqa: BLE001
        return [], f"error:{type(e).__name__}"
    if r.status_code != 200:
        return [], f"http:{r.status_code}"
    try:
        d = json.loads(r.text)
    except json.JSONDecodeError:
        return [], "not_json"
    out = []
    for item in d.get("list", []):
        # 360 的 `thumb` 是 240px 缩略图；`img` 才是原图/大图。
        url = item.get("img") or item.get("imgurl") or item.get("thumb") or ""
        if not url.startswith("http") or SKIP_IMG_RE.search(url):
            continue
        out.append({"url": url, "thumb_url": item.get("thumb", ""),
                    "source_url": item.get("link", "") or "",
                    "title": (item.get("title") or "")[:80],
                    "width": int(item.get("width") or 0),
                    "height": int(item.get("height") or 0),
                    "channel": "360",
                    "referer": "https://image.so.com/"})
        if len(out) >= limit:
            break
    return out, ("ok" if out else "empty")


def _search_baidu(query: str, limit: int) -> tuple[list[dict], str]:
    """百度图片 acjson 端点。"""
    out = []
    try:
        r = requests.get("https://image.baidu.com/search/acjson",
                         params={"tn": "resultjson_com", "logid": "1", "ipn": "rj",
                                 "word": query, "pn": 0, "rn": max(30, limit)},
                         headers={"User-Agent": UA,
                                  "Referer": "https://image.baidu.com/"},
                         timeout=20)
        d = json.loads(r.text.replace("\\'", "'"))
    except Exception:  # noqa: BLE001
        return out
    for item in d.get("data", []):
        url = item.get("objURL") or item.get("hoverURL") or ""
        if not url.startswith("http"):
            url = item.get("hoverURL") or ""
        if not url.startswith("http") or SKIP_IMG_RE.search(url):
            continue
        title = re.sub(r"<[^>]+>", "", item.get("fromPageTitleEnc", "") or item.get("fromPageTitle", ""))
        out.append({"url": url, "thumb_url": item.get("thumbURL", ""), "title": title[:80]})
        if len(out) >= limit:
            break
    return out, ("ok" if out else "empty")


def _search_bing(query: str, limit: int) -> tuple[list[dict], str]:
    """Bing 中国图片搜索兜底（本环境实测常返回无关内容，由相关性护栏兜住）。"""
    out = []
    seen = set()
    for first in (1, 36):
        url = (f"https://cn.bing.com/images/async?q={quote(query)}"
               f"&first={first}&count=35&mmasync=1")
        r = requests.get(url, headers={"User-Agent": UA,
                                       "Referer": "https://cn.bing.com/images/"}, timeout=20)
        if r.status_code != 200:
            break
        for m in re.finditer(r"m=(\"[^\"]*\"|'[^']*')", r.text):
            import html as _html
            try:
                meta = json.loads(_html.unescape(m.group(1)[1:-1]))
            except json.JSONDecodeError:
                continue
            murl = meta.get("murl", "")
            if murl.startswith("http") and murl not in seen and not SKIP_IMG_RE.search(murl):
                seen.add(murl)
                out.append({"url": murl, "thumb_url": meta.get("turl", ""),
                            "title": meta.get("t", "")[:80]})
            if len(out) >= limit:
                return out[:limit], "ok"
        if len(out) >= limit:
            break
        time.sleep(SLEEP_SECONDS)
    return out[:limit], ("ok" if out else "empty")


VIEW_QUERIES = {  # 视角词 → (查询后缀, 初始视角标签——机器猜测, 证据记查询词, 人工可改)
    "hero": ("45度", "hero_45"),   # v0.2.5: 查询词只标粗类（禁冒充左右定向, 意见 #8）
    "side": ("侧视图", "side"),
    "front": ("正前", "front"),
    "rear": ("尾部", "rear"),
    "interior": ("内饰", "interior"),
}


def crawl_model_views(conn, data_dir: Path, vehicle_id: str, vehicle_name: str, *,
                      views=("hero", "side", "rear"), per_view: int = 3,
                      query_extra: str = "", batch_id: str | None = None,
                      license: str = "web_third_party") -> dict:
    """分视角搜图（角度缺口驱动）: 每视角独立查询词 → 初始视角标签 + 证据记录。"""
    report = {"vehicle": vehicle_name, "views": {}, "batch_id": batch_id}
    for key in views:
        suffix, guess = VIEW_QUERIES[key]
        q = f"{vehicle_name} {query_extra} {suffix}".strip()
        rep = crawl_model_images(conn, data_dir, vehicle_id, q,
                                 limit=per_view, license=license,
                                 batch_id=batch_id, view_guess=guess)
        report["views"][key] = {"query": q, "candidates": rep["candidates"],
                                "gate_blocked": rep["gate_blocked"], "found": rep["found"],
                                "existing": rep["existing"]}
        report["batch_id"] = rep["batch_id"]
    return report


HD_SUFFIX_RE = re.compile(r"!(\d{3,4})$")
HD_SUFFIX = "!1200"


def upgrade_image_url(url: str) -> str | None:
    """把 CDN 的缩放后缀（`!600`/`!550`）换成 `!1200` 取大图。

    实测（2026-11-09）：13 张带后缀的参考图里 **11 张**能从 550–640px 升到
    1200×800，直接由“参考层”变成“部件可用”（http 401/403 的两张回落原图）。
    只认纯数字后缀，`!news.pc` 这类跳过；已经是 ≥1200 的不再动。
    """
    m = HD_SUFFIX_RE.search(url or "")
    if m and int(m.group(1)) < 1200:
        return url[:m.start()] + HD_SUFFIX
    # 搜狐图床：/q_70,c_zoom,w_640/ 里的 w_640 可以改成 w_1280（实测 640x426→1280x852）
    m2 = re.search(r"w_(\d{2,4})", url or "")
    if m2 and int(m2.group(1)) < 1280:
        return url[:m2.start()] + "w_1280" + url[m2.end():]
    return None


class _ImgParser(HTMLParser):
    """只收 <img> 的 src/data-src/data-original，不判断内容。"""

    def __init__(self) -> None:
        super().__init__()
        self.srcs: list[str] = []

    def handle_starttag(self, tag, attrs):  # noqa: D401
        if tag.lower() != "img":
            return
        d = dict(attrs)
        u = d.get("data-src") or d.get("data-original") or d.get("src") or ""
        if u:
            self.srcs.append(u)


def extract_page_images(html: str, page_url: str, limit: int = 12) -> list[str]:
    """从图集/文章页 HTML 里抽图片 URL（绝对化、去重、去小图标）。"""
    from urllib.parse import urljoin

    p = _ImgParser()
    try:
        p.feed(html or "")
    except Exception:  # noqa: BLE001
        return []
    seen, out = set(), []
    for raw in p.srcs:
        u = urljoin(page_url, raw.strip())
        if not u.startswith("http") or SKIP_IMG_RE.search(u):
            continue
        base = re.sub(r"!\d{3,4}$", "", u)
        if base in seen:
            continue
        seen.add(base)
        out.append(u)
        if len(out) >= limit:
            break
    return out


ARTICLE_DOMAINS = ("360che.com", "chinatruck.org", "sohu.com", "yoojia.com",
                   "baijiahao.baidu.com", "yidianzixun.com", "cn357.com")
B2B_DOMAINS = ("alibaba.com", "cmo2o.com", "1688.com", "made-in-china.com",
               "dealer.360che.com", "product.")


def page_priority(url: str) -> int:
    """来源页打分：资讯/图集页优先，B2B 商品页直接排除（返回 -1）。

    实测 360 结果的 `link` 里 dealer/alibaba 占比高，回访这些页产出几乎为 0；
    而资讯页一页能出 10–30 张图。
    """
    u = (url or "").lower()
    if any(d in u for d in B2B_DOMAINS):
        return -1
    score = 0
    if any(d in u for d in ARTICLE_DOMAINS):
        score += 2
    for seg in ("/tech/", "/news/", "/a/", "/article/", "/pic/", "/photo/"):
        if seg in u:
            score += 1
            break
    return score


def harvest_source_page(source_url: str, limit: int = 8) -> list[dict]:
    """回访来源页（文章/图集），抽出同页图片并升级到大图。

    背景：360 图片 API 每条结果都带 `link`（来源页），一个 360che 文章页实测有
    30 张图、抽样 7/8 能升到 1200×800；而图片搜索每查询只出 ~1.8 张部件可用。
    所以“搜索找页 → 回访取全页图”比“只取搜索结果里的单张”产出高得多。
    """
    if not source_url.startswith("http"):
        return []
    try:
        r = requests.get(source_url, headers={"User-Agent": UA}, timeout=20)
        if r.status_code != 200:
            return []
        html = r.text
    except Exception:  # noqa: BLE001
        return []
    hits = []
    for u in extract_page_images(html, source_url, limit=limit):
        hits.append({"url": upgrade_image_url(u) or u,
                     "thumb_url": "", "title": "", "width": 0, "height": 0,
                     "channel": "page", "source_url": source_url,
                     "referer": source_url})
    return hits


def _fetch_image(url: str, referer: str) -> bytes:
    src = quote(url, safe=":/?&=%._-#")
    r = requests.get(src, headers={"User-Agent": UA, "Referer": referer},
                     timeout=20, stream=True)
    if r.status_code != 200:
        raise ValueError(f"http {r.status_code}")
    data = b""
    for chunk in r.iter_content(65536):
        data += chunk
        if len(data) > MAX_IMG_BYTES:
            raise ValueError("图片超过 8MB")
    return data


def _download_and_gate(hit: dict) -> dict:
    """下载+门卫（线程池内跑; SQLite 入库只在主线程做）。

    先试“大图后缀”（`!1200`），失败再回落到原始 URL——这是本环境最便宜的
    分辨率提升手段（无登录/无额外请求数）。
    """
    out = {"hit": hit, "data": None, "gate": None, "error": None,
           "url_used": hit.get("url", ""), "upgraded": False}
    referer = (hit.get("referer")
               or CHANNEL_REFERERS.get(hit.get("channel", ""))
               or "https://image.so.com/")
    big = upgrade_image_url(hit.get("url", ""))
    attempts = [u for u in (big, hit.get("url", "")) if u]
    last_err = None
    for i, src_url in enumerate(attempts):
        try:
            data = _fetch_image(src_url, referer)
            from PIL import Image
            from io import BytesIO
            pre = gate.prefilter(data)
            out["prefilter"] = pre
            out["url_used"] = src_url
            out["upgraded"] = bool(big) and i == 0
            if not pre["ok"]:
                # 第一段（确定性）已否决：不进 CLIP，省一次推理；理由如实回传
                out["data"] = data
                out["gate"] = {"pass": False, "stage": "prefilter",
                               "reasons": list(pre["reasons"]), "margin": None,
                               "keep": None, "drop": None, "scene": None,
                               "keep_label": "", "drop_label": ""}
                out["error"] = None
                return out
            if Image.open(BytesIO(data)).size[0] < MIN_IMG_WIDTH:
                raise ValueError("图片过小")
            out["data"] = data
            out["gate"] = gate.check(data)
            out["error"] = None
            return out
        except Exception as e:  # noqa: BLE001
            last_err = e
    out["error"] = str(last_err)
    return out


def crawl_model_images(conn, data_dir: Path, vehicle_id: str, vehicle_name: str,
                       query: str | None = None, *, limit: int = 6,
                       license: str = "web_third_party",
                       batch_id: str | None = None,
                       view_guess: str | None = None) -> dict:
    """按型号搜图并入库（弱关联 provisional 挂载）。
    速度（2026-10-17）: 图片下载线程池并行（此前逐张串行+每张硬睡 1s,
    12 车型全量检索不可接受——产品负责人反馈"整个流程太长"）。"""
    from concurrent.futures import ThreadPoolExecutor
    query = query or f"{vehicle_name} 牵引车"
    batch_id = batch_id or f"batch-img-{uuid.uuid4().hex[:10]}"
    report = {"vehicle": vehicle_name, "vehicle_id": vehicle_id, "query": query,
              "batch_id": batch_id, "found": 0, "candidates": 0, "existing": 0,
              "gate_blocked": 0, "skipped": 0, "items": []}

    hits = search_images(query, limit=limit * 2)  # 多取, 过滤后保量
    report["found"] = len(hits)
    time.sleep(SLEEP_SECONDS)  # 查询间礼让（下载已并行, 不逐张睡）
    with ThreadPoolExecutor(max_workers=6) as ex:
        downloads = list(ex.map(_download_and_gate, hits))
    for res in downloads:
        hit, g, data = res["hit"], res["gate"], res["data"]
        if report["candidates"] >= limit:
            break
        if res["error"] is not None:
            report["skipped"] += 1
            report["items"].append({"src": hit["url"][:80],
                                    "status": f"跳过: {res['error']}"})
            continue
        if not g["pass"]:
            report["gate_blocked"] += 1
            report["items"].append({"src": hit["url"][:80],
                                    "status": f"门卫拦截(margin={g['margin']})"})
            continue
        qflags = ["multi_vehicle"] if g.get("scene") == "multi_vehicle" else []
        result = ingest.ingest_file_bytes(
            conn, data_dir, name=Path(hit["url"].split("?")[0]).name or "search.jpg",
            data=data, platform=f"图片搜索({query})", license=license,
            batch_id=batch_id, vehicle_id=vehicle_id,
            binding_evidence="co_occurrence_only",  # T3 弱关联: 搜索词声称, 待人工确认
            view_angle=view_guess or "untagged",
            quality_flags=qflags,
            evidence_note=f"搜索词声称: {query}｜图题: {hit['title'] or '(无)'}｜门卫 margin={g['margin']}",
            source_url=hit["url"])
        if result["status"] in ("merged", "source_exists"):
            report["existing"] += 1
        else:
            report["candidates"] += 1
        report["items"].append({"src": hit["url"][:80], "status": result["status"],
                                "asset_id": result["asset_id"]})
    return report
