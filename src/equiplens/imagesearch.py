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
SKIP_IMG_RE = re.compile(r"\.(svg|gif|ico)(\?|$)|logo|icon|banner|qrcode", re.I)


def search_images(query: str, limit: int = 12) -> list[dict]:
    """按型号搜图：多通道 + 健康检查 + 相关性护栏。

    通道顺序：360 图片 → 百度 → Bing。每个通道返回后先过"相关性护栏"
    （标题须含查询短语或其任一 token），不相关则记 `unrelated` 并换下一个通道；
    被反爬/验证页拦截记 `blocked`。全部失败返回空，由调用方如实上报，不拿垃圾充数。
    """
    hits, _ = search_images_ex(query, limit)
    return hits


def search_model_images(model: str, limit: int = 12) -> tuple[list[dict], list[dict]]:
    """按型号取图：两段查询阶梯（型号+工程车 → 型号），合并去重并记录每段诊断。"""
    seen: set[str] = set()
    out: list[dict] = []
    diag: list[dict] = []
    for q in (f"{model} 工程车", model):
        hits, d = search_images_ex(q, limit, model=model)
        diag.append({"query": q, "channels": d})
        for h in hits:
            if h["url"] in seen:
                continue
            seen.add(h["url"])
            out.append(h)
            if len(out) >= limit:
                return out, diag
    return out, diag


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
        url = item.get("imgurl") or item.get("thumb") or ""
        if not url.startswith("http") or SKIP_IMG_RE.search(url):
            continue
        out.append({"url": url, "thumb_url": item.get("thumb", ""),
                    "title": (item.get("title") or "")[:80]})
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


def _download_and_gate(hit: dict) -> dict:
    """下载+门卫（线程池内跑; SQLite 入库只在主线程做）。"""
    out = {"hit": hit, "data": None, "gate": None, "error": None}
    try:
        src = quote(hit["url"], safe=":/?&=%._-#")
        r = requests.get(src, headers={"User-Agent": UA, "Referer": hit["url"]},
                         timeout=20, stream=True)
        data = b""
        for chunk in r.iter_content(65536):
            data += chunk
            if len(data) > MAX_IMG_BYTES:
                raise ValueError("图片超过 8MB")
        from PIL import Image
        from io import BytesIO
        if Image.open(BytesIO(data)).size[0] < MIN_IMG_WIDTH:
            raise ValueError("图片过小")
        out["data"] = data
        out["gate"] = gate.check(data)
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)
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
