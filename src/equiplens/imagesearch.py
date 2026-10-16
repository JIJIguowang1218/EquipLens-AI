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
    """按型号搜图：百度图片优先（产品负责人工作流同源、中文命中准），
    Bing 中国图片兜底（查询词加引号防拆词）。返回 [{url, thumb_url, title}]。"""
    out = _search_baidu(query, limit)
    if len(out) < limit:
        out += [h for h in _search_bing(f'"{query}"', limit) if h["url"] not in {x["url"] for x in out}]
    return out[:limit]


def _search_baidu(query: str, limit: int) -> list[dict]:
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
    return out


def _search_bing(query: str, limit: int) -> list[dict]:
    """Bing 中国图片搜索兜底。"""
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
                return out
        if len(out) >= limit:
            break
        time.sleep(SLEEP_SECONDS)
    return out[:limit]


VIEW_QUERIES = {  # 视角词 → (查询后缀, 初始视角标签——机器猜测, 证据记查询词, 人工可改)
    "hero": ("45度", "hero_lf"),
    "side": ("侧视图", "side_l"),
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
                                "gate_blocked": rep["gate_blocked"], "found": rep["found"]}
        report["batch_id"] = rep["batch_id"]
    return report


def crawl_model_images(conn, data_dir: Path, vehicle_id: str, vehicle_name: str,
                       query: str | None = None, *, limit: int = 6,
                       license: str = "web_third_party",
                       batch_id: str | None = None,
                       view_guess: str | None = None) -> dict:
    """按型号搜图并入库（弱关联 provisional 挂载）。"""
    query = query or f"{vehicle_name} 牵引车"
    batch_id = batch_id or f"batch-img-{uuid.uuid4().hex[:10]}"
    report = {"vehicle": vehicle_name, "vehicle_id": vehicle_id, "query": query,
              "batch_id": batch_id, "found": 0, "candidates": 0, "existing": 0,
              "gate_blocked": 0, "skipped": 0, "items": []}

    hits = search_images(query, limit=limit * 2)  # 多取, 过滤后保量
    report["found"] = len(hits)
    for hit in hits:
        if report["candidates"] >= limit:
            break
        time.sleep(SLEEP_SECONDS)
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
            g = gate.check(data)
            if not g["pass"]:
                report["gate_blocked"] += 1
                report["items"].append({"src": hit["url"][:80],
                                        "status": f"门卫拦截(margin={g['margin']})"})
                continue
            qflags = ["multi_vehicle"] if g.get("scene") == "multi_vehicle" else []
            result = ingest.ingest_file_bytes(
                conn, data_dir, name=Path(hit["url"].split("?")[0]).name or "search.jpg",
                data=data, platform=f"Bing图片搜索({query})", license=license,
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
        except Exception as e:  # noqa: BLE001
            report["skipped"] += 1
            report["items"].append({"src": hit["url"][:80], "status": f"跳过: {e}"})
    return report
