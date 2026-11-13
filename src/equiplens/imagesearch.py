"""搜索渠道（主通道 360 图片；百度/Bing 仅在 360 结果不足时兜底）。

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


def search_platforms(query: str, limit: int = 6, *,
                    model: str | None = None,
                    platforms: tuple[str, ...] = ("360", "baidu")) -> tuple[list[dict], list[dict]]:
    """平台层显式组合，并在**下载前**复用 _relevant 护栏。

    正常 search_images_ex 会先 360 命中就停；平台实验需要 360+Baidu 都取一些，
    所以单独组合，但不能绕过正常路径已有的相关性预筛。
    """
    fns = {"360": _search_360, "baidu": _search_baidu, "bing": _search_bing}
    out, seen, diag = [], set(), []
    for name in platforms:
        fn = fns.get(name)
        if not fn:
            continue
        try:
            got, status = fn(query, max(limit, 12))
        except Exception as e:  # noqa: BLE001
            got, status = [], f"error:{type(e).__name__}"
        rel = [h for h in got if _relevant(query, h.get("title", ""), model)]
        diag.append({"channel": name, "returned": len(got),
                     "relevant": len(rel), "filtered": len(got) - len(rel),
                     "status": status})
        for h in rel:
            u = h.get("url", "")
            if not u or u in seen:
                continue
            seen.add(u)
            h = dict(h)
            h["channel"] = name
            out.append(h)
            if len(out) >= limit:
                return out, diag
    return out, diag


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


def alias_query(src: str) -> str:
    """把“拉丁品牌/型号 + 括号说明”的车型名改写成 360 更容易命中的中文查询。

    实测（2026-11-10）：`Zetros 4051 AS 6x6` 在 360 返回的是列宁格勒/MAN/卡玛兹，
    而 `奔驰 Zetros 6x6 牵引车` 能返回 6 张真车图——纯拉丁型号名在中文图库
    里召回极差，必须补中文品牌或去掉冷门型号码。
    """
    s = re.sub(r"[（(][^）)]*[）)]", " ", src or "")
    toks = _tokens(s)
    group = _brand_group(s)
    brand = ""
    if group:
        brand = next((a for a in group if re.search(r"[\u4e00-\u9fff]", a)), "")
        if not brand and group[0] not in _BRAND_LOOKUP:
            brand = group[0]  # 未知拉丁车系（Zetros）：保留，别丢
    series = next((t for t in toks if re.search(r"[a-z]", t) and not re.search(r"\d", t)
                   and len(t) >= 3 and t not in GENERIC and t not in group), "")
    code = next((t for t in _distinctive(s) if t not in group), "")
    conf = next((c for c in ("6x6", "8x8", "4x4") if c in _config_set(src or s)), "")
    tail = "牵引车" if "牵引" in s else "卡车"
    if not (brand or series or code):   # 只有构型词（6x6 牵引车）也是噪声：跳过该档
        return ""
    core = [p for p in (brand, series or code, conf) if p]
    return " ".join(core + [tail]).strip()


def query_variants(query: str, model: str = "") -> list[str]:
    """一次抓取的查询阶梯：规划器 query → 车型全名 → 中文别名改写。"""
    out: list[str] = []
    for q in (query, model, alias_query(model or query)):
        q = (q or "").strip()
        if q and q not in out:
            out.append(q)
    return out


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
                 "专用车", "越野", "底盘", "驾驶室", "油井", "矿卡", "运输",
                 "truck", "lorry", "tractor", "tipper", "dump", "chassis",
                 "offroad", "off-road", "vehicle", "camion")

# 中外品牌别名：模型名常是拉丁文（Volvo/KAMAZ），标题却是中文（沃尔沃/卡玛斯）。
# 护栏按“同组任一并集命中”判断，否则这些车型在 360 上永远被判不相关。
BRAND_GROUPS = (
    ("volvo", "沃尔沃"),
    ("kamaz", "卡玛斯", "卡玛兹"),
    ("mercedes", "benz", "奔驰", "梅赛德斯"),
    ("man", "曼恩", "曼"),
    ("scania", "斯堪尼亚"),
    ("iveco", "依维柯"),
    ("renault", "雷诺"),
    ("daf", "达夫"),
    ("tatra", "太脱拉", "太拖拉"),
    ("hino", "日野"),
    ("isuzu", "五十铃"),
    ("mitsubishi", "三菱"),
    ("mack", "马克"),
    ("kenworth", "肯沃斯"),
    ("peterbilt", "彼得比尔特"),
    ("sany", "三一"),
    ("zoomlion", "中联"),
    ("xcmg", "徐工"),
    ("shacman", "陕汽"),
    ("howo", "豪沃"),
    ("dongfeng", "东风"),
    ("beiben", "北奔"),
)
_BRAND_LOOKUP: dict[str, tuple[str, ...]] = {}
for _group in BRAND_GROUPS:
    for _name in _group:
        _BRAND_LOOKUP[_name] = _group


CONF_RE = re.compile(r"\d+\s*[x×]\s*\d+", re.I)


def _config_tokens(s: str) -> list[str]:
    """构型词（6x6/8x8/4x2）。"""
    return [re.sub(r"[×\s]", "x", m).lower() for m in CONF_RE.findall(s)]


CONF_WORDS = {"6x6": ("6x6", "6驱", "六驱"),
              "8x8": ("8x8", "8驱", "八驱"),
              "4x4": ("4x4", "4驱", "四驱")}


def _config_set(s: str) -> set[str]:
    """构型集合（含“六驱/6驱”这类中文写法）。"""
    out = set(_config_tokens(s))
    low = (s or "").lower().replace("×", "x")
    for code, words in CONF_WORDS.items():
        if any(w in low for w in words):
            out.add(code)
    return out


def _distinctive(model: str) -> list[str]:
    """型号里“能唯一定位到这台车”的字母数字串（NG80 / CA2191P2K2T / X3000 / C7H）。

    必须同时含字母和数字：`4051` / `800` 这类纯数字太泛，会把“800ml”这种
    正文当车型命中（MOL 那次就是这么混进来的）。
    """
    return [t for t in _tokens(model)
            if re.search(r"[a-z]", t) and re.search(r"\d", t)
            and t not in GENERIC and len(t) >= 3]


def _alias_in(name: str, text: str) -> bool:
    """品牌别名是否出现在标题里；拉丁别名按词边界匹配，避免 man ⊂ human。"""
    if not name:
        return False
    if re.fullmatch(r"[a-z0-9\-]+", name):
        return re.search(rf"(?<![a-z0-9]){re.escape(name)}(?![a-z0-9])", text) is not None
    return name in text


# 描述性词干：含这些词的词不是品牌（“油田专用全驱牵引车”“6x6 越野牵引头”）
_DESC_STEMS = ("牵引", "挂车", "卡车", "货车", "自卸", "载货", "越野", "全驱",
               "驱动", "专用", "运输", "工程", "起重", "油井", "矿卡", "沙漠",
               "油田", "井场", "重型", "中型", "轻型", "底盘", "驾驶室", "特种",
               "轮胎", "发动机", "驾驶")


def _looks_like_brand(tok: str) -> bool:
    """短中文词、不含描述性词干，才允许当品牌兜底；拉丁车系（Zetros/Oshkosh）直接认。"""
    if not tok:
        return False
    if re.fullmatch(r"[A-Za-z][A-Za-z\-]+", tok):
        return True
    if re.search(r"\d", tok) or len(tok) > 4:
        return False
    return not any(s in tok for s in _DESC_STEMS)


def _brand_group(src: str) -> tuple[str, ...]:
    """取车型名里的品牌别名组。

    2026-11-13 修复：旧实现把“第一个非数字词”当品牌，导致描述性车名
    （`油田专用全驱牵引车`、`6x6 越野牵引头`）被当成品牌去要求标题命中，
    该车型所有搜索命中被相关性护栏判死 → 目标 0 图（历史 108 次 no_hits）。
    现在只认别名表；长描述里内嵌的品牌按子串识别；兜底词必须是品牌样。
    """
    toks = _tokens(src)
    for t in toks:
        if t in _BRAND_LOOKUP:
            return _BRAND_LOOKUP[t]
    # 兜底只认**开头**的词：品牌通常在车名最前面；“马力/轴距/批次”这类
    # 后半段属性词不能被当成品牌，否则又会回到“要求标题出现属性词”的误杀。
    if toks:
        first = toks[0]
        if first not in GENERIC and _looks_like_brand(first):
            return (first,)
    # 长描述里内嵌的品牌：只在括号外找，避免把“沃尔沃发动机”当成品牌
    low = re.sub(r"[（(][^）)]*[）)]", " ", src or "").lower()
    if low:
        for alias, group in _BRAND_LOOKUP.items():
            if alias and alias in low:
                return group
    return ()


def _relevant(query: str, title: str, model: str | None = None) -> bool:
    """相关性护栏（型号优先，召回优先）：

    1) 标题含"非车污染词"（解放战争/壁纸/动漫…）→ 直接判不相关；
    2) 标题明确写了一个**冲突构型**（车型 6x6、标题 6x2）→ 不相关；
       标题没写构型不判死（大量中文标题只写"六驱"或干脆不写）；
    3) 型号代码（NG80/X3000/C7H…）命中 → 最强，直接通过；
    4) 否则要求品牌（含中外别名）命中 + 车辆词；没有品牌才只要求车辆词。
    """
    t = (title or "").lower()
    if not t:
        return False
    if any(w in t for w in NON_VEHICLE):
        return False
    src = model or query
    want = _config_set(src)
    have = _config_set(t)
    if want and have and not (want & have):
        return False  # 6x6 车型遇到 6x2 标题：明确矛盾
    codes = _distinctive(src)
    if codes and any(c in t for c in codes):
        return True  # 型号代码直接命中：最强
    # 代码没命中时退回"品牌 + 车辆词"（召回优先；身份真伪交给门卫 + 人工）
    group = _brand_group(src)
    if group:
        if any(_alias_in(a, t) for a in group):
            return True
        return False
    # 无品牌/车系：用车名自身的非通用词与标题做重叠（不查类目表），再退回车辆词。
    own = [x for x in _tokens(src)
           if not re.search(r"\d", x) and x not in GENERIC and len(x) >= 2]
    if own and any(x in t for x in own):
        return True
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
    except Exception as e:  # noqa: BLE001
        # 必须返回 (hits, status)：调用方按元组解包，返回 list 会炸成 error:ValueError
        return out, f"error:{type(e).__name__}"
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


REFERER_FALLBACKS = ("https://image.so.com/", "")


def download_candidates(url: str) -> list[str]:
    """同一张图的候选 URL：先大图后缀，再原样，最后去后缀的裸图。"""
    out = []
    up = upgrade_image_url(url)
    if up:
        out.append(up)
    if url and url not in out:
        out.append(url)
    base = re.sub(r"!\d{3,4}$", "", url or "")
    if base and base != url and base not in out:
        out.append(base)
    return out[:3]


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


class DomainHealth:
    """按 host 记录下载硬失败（403/401/404/DNS/连接），连续 N 次即拉黑。

    背景（2026-11-10 E20/T48）：失败 URL 阶梯重放 0/12，同 URL 重试无收益；
    反复请求同一批死图床只会烧时间。拉黑后直接跳过，把尝试预算让给别的候选。
    """

    HARD_HINTS = ("http 403", "http 401", "http 404", "getaddrinfo",
                  "nameresolution", "name resolution", "connection",
                  "timed out", "timeout", "ssl")

    def __init__(self, threshold: int = 3):
        self.threshold = max(1, int(threshold))
        self.fails: dict[str, int] = {}
        self.blocked: set[str] = set()

    @staticmethod
    def host(url: str) -> str:
        try:
            from urllib.parse import urlparse
            return (urlparse(url or "").hostname or "").lower()
        except ValueError:
            return ""

    def is_blocked(self, url: str) -> bool:
        return self.host(url) in self.blocked

    def record(self, url: str, error) -> None:
        h = self.host(url)
        if not h:
            return
        text = str(error or "").lower()
        if not any(k in text for k in self.HARD_HINTS):
            return
        self.fails[h] = self.fails.get(h, 0) + 1
        if self.fails[h] >= self.threshold:
            self.blocked.add(h)

    def stats(self) -> dict:
        return {"blocked_hosts": sorted(self.blocked),
                "fail_counts": dict(sorted(self.fails.items()))}


def _download_and_gate(hit: dict, health: "DomainHealth | None" = None) -> dict:
    """下载 + 两段式门卫。

    候选顺序：大图后缀（`!1200`）→ 原 URL → 去后缀裸图；
    每档再试 Referer（来源 → image.so.com → 无），最多 6 次，覆盖 403/404/超时。

    `health`：按 host 学习的失败表；已拉黑的域名直接跳过（不消耗 tries）。
    """
    out = {"hit": hit, "data": None, "gate": None, "error": None,
           "url_used": hit.get("url", ""), "upgraded": False, "tries": 0}
    if health is not None and health.is_blocked(hit.get("url", "")):
        out["error"] = "domain_blocked"
        return out
    referer = (hit.get("referer")
               or CHANNEL_REFERERS.get(hit.get("channel", ""))
               or "https://image.so.com/")
    urls = download_candidates(hit.get("url", ""))
    refs: list[str] = []
    for r in [referer, *REFERER_FALLBACKS]:
        if r not in refs:
            refs.append(r)
    big = upgrade_image_url(hit.get("url", "")) or ""
    last_err = None
    tries = 0
    for src_url in urls:
        for ref in refs:
            tries += 1
            if tries > 6:
                break
            try:
                data = _fetch_image(src_url, ref)
            except Exception as e:  # noqa: BLE001
                last_err = e
                continue
            from PIL import Image
            from io import BytesIO
            pre = gate.prefilter(data)
            out["prefilter"] = pre
            out["url_used"] = src_url
            out["upgraded"] = bool(big) and src_url == big
            out["tries"] = tries
            if not pre["ok"]:
                out["data"] = data
                out["gate"] = {"pass": False, "stage": "prefilter",
                               "reasons": list(pre["reasons"]), "margin": None,
                               "keep": None, "drop": None, "scene": None,
                               "keep_label": "", "drop_label": ""}
                out["error"] = None
                return out
            try:
                if Image.open(BytesIO(data)).size[0] < MIN_IMG_WIDTH:
                    raise ValueError("图片过小")
            except Exception as e:  # noqa: BLE001
                last_err = e
                continue
            out["data"] = data
            out["gate"] = gate.check(data)
            out["error"] = None
            return out
    out["tries"] = tries
    out["error"] = str(last_err)
    if health is not None:
        health.record(hit.get("url", ""), last_err)
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
