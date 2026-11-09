"""P2-W2 源路由：健康度、熔断、24h 缓存、SearXNG/Tavily 适配器骨架。

原则：源是适配器；路由只负责顺序、健康、缓存，不替源做判断。
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Callable

import requests


class SourceHealth:
    """按源记录成功/被拦/空结果；连续失败触发熔断。"""

    def __init__(self, path: str | Path, *, failure_threshold: int = 2,
                 cooldown_seconds: int = 300):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        return {"sources": {}}

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        tmp.replace(self.path)

    def record(self, name: str, status: str) -> None:
        rec = self.data["sources"].setdefault(name, {
            "calls": 0, "blocked": 0, "empty": 0, "ok": 0,
            "consecutive_failures": 0, "open_until": 0, "last_status": ""})
        rec["calls"] += 1
        rec["last_status"] = status
        if status.startswith("blocked") or status.startswith("error"):
            rec["blocked"] += 1
            rec["consecutive_failures"] += 1
            if rec["consecutive_failures"] >= self.failure_threshold:
                rec["open_until"] = time.time() + self.cooldown_seconds
        elif status == "empty":
            rec["empty"] += 1
            rec["consecutive_failures"] = 0
        else:
            rec["ok"] += 1
            rec["consecutive_failures"] = 0
            rec["open_until"] = 0
        self._save()

    def is_open(self, name: str) -> bool:
        rec = self.data["sources"].get(name) or {}
        return float(rec.get("open_until") or 0) > time.time()

    def summary(self) -> dict:
        return dict(self.data.get("sources") or {})


class SearchCache:
    """24h 查询缓存：同一 query/limit/model 不重复打源。"""

    def __init__(self, path: str | Path, *, ttl_seconds: int = 86400):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_seconds
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        return {}

    def _key(self, query: str, limit: int, model: str | None) -> str:
        raw = json.dumps([query, limit, model], ensure_ascii=False)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def get(self, query: str, limit: int, model: str | None) -> list[dict] | None:
        item = self.data.get(self._key(query, limit, model))
        if not item:
            return None
        if time.time() - float(item.get("ts", 0)) > self.ttl:
            return None
        return item.get("hits")

    def put(self, query: str, limit: int, model: str | None,
            hits: list[dict]) -> None:
        self.data[self._key(query, limit, model)] = {
            "ts": time.time(), "query": query, "limit": limit,
            "model": model, "hits": hits}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        tmp.replace(self.path)


class SourceRouter:
    """按顺序尝试源；被拦/空结果换下一个；支持熔断与缓存。"""

    def __init__(self, sources: list[tuple[str, Callable]],
                 health: SourceHealth, cache: SearchCache | None = None):
        self.sources = sources
        self.health = health
        self.cache = cache

    def search(self, query: str, limit: int = 12,
               model: str | None = None) -> tuple[list[dict], list[dict]]:
        if self.cache:
            cached = self.cache.get(query, limit, model)
            if cached:
                return cached, [{"channel": "cache", "status": "cached",
                                 "returned": len(cached)}]
        diag: list[dict] = []
        for name, fn in self.sources:
            if self.health.is_open(name):
                diag.append({"channel": name, "status": "circuit_open",
                             "returned": 0})
                continue
            try:
                hits, status = fn(query, limit, model)
            except Exception as e:  # noqa: BLE001
                hits, status = [], f"error:{type(e).__name__}"
            hits = list(hits or [])
            self.health.record(name, str(status))
            diag.append({"channel": name, "status": str(status),
                         "returned": len(hits)})
            if hits:
                if self.cache:
                    self.cache.put(query, limit, model, hits)
                return hits, diag
        return [], diag


# ---------------------------------------------------------------- direct 360
def source_360(query: str, limit: int = 12,
               model: str | None = None) -> tuple[list[dict], str]:
    from .. import imagesearch
    got, status = imagesearch._search_360(query, max(limit, 12))
    rel = [h for h in got
           if imagesearch._relevant(query, h.get("title", ""), model)]
    for h in rel:
        h.setdefault("channel", "360")
    return rel[:limit], status


# ---------------------------------------------------------------- searxng
class SearxngSource:
    """SearXNG 图片检索适配器：自托管实例的 /search?format=json。"""

    def __init__(self, base_url: str, *, timeout: int = 20):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def __call__(self, query: str, limit: int = 12,
                 model: str | None = None) -> tuple[list[dict], str]:
        try:
            r = requests.get(f"{self.base_url}/search",
                             params={"q": query, "format": "json",
                                     "categories": "images", "pageno": 1},
                             headers={"User-Agent": "EquipLensResearch/0.1"},
                             timeout=self.timeout)
        except Exception as e:  # noqa: BLE001
            return [], f"error:{type(e).__name__}"
        if r.status_code != 200:
            return [], f"http:{r.status_code}"
        try:
            data = r.json()
        except Exception:  # noqa: BLE001
            return [], "not_json"
        out = []
        for item in data.get("results", []):
            url = item.get("img_src") or item.get("thumbnail_src") or item.get("url")
            if not url:
                continue
            title = item.get("title") or ""
            if model:
                from .. import imagesearch
                if not imagesearch._relevant(query, title, model):
                    continue
            out.append({"url": url, "title": title[:120],
                        "width": int(item.get("width") or 0),
                        "height": int(item.get("height") or 0),
                        "channel": "searxng",
                        "referer": self.base_url})
            if len(out) >= limit:
                break
        return out, ("ok" if out else "empty")


# ---------------------------------------------------------------- tavily
class TavilySource:
    """Tavily 搜索 API 骨架（include_images=true）；需 API key。"""

    def __init__(self, api_key: str, *, endpoint: str = "https://api.tavily.com/search",
                 timeout: int = 30):
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout

    def __call__(self, query: str, limit: int = 12,
                 model: str | None = None) -> tuple[list[dict], str]:
        try:
            r = requests.post(self.endpoint, json={
                "api_key": self.api_key, "query": query,
                "search_depth": "basic", "include_images": True,
                "max_results": limit}, timeout=self.timeout)
        except Exception as e:  # noqa: BLE001
            return [], f"error:{type(e).__name__}"
        if r.status_code != 200:
            return [], f"http:{r.status_code}"
        try:
            data = r.json()
        except Exception:  # noqa: BLE001
            return [], "not_json"
        out = []
        for img in data.get("images") or []:
            if isinstance(img, str):
                url, title = img, query
            elif isinstance(img, dict):
                url = img.get("url") or img.get("img_src")
                title = img.get("title") or query
            else:
                continue
            if not url:
                continue
            out.append({"url": url, "title": str(title)[:120],
                        "channel": "tavily", "referer": "https://tavily.com/"})
            if len(out) >= limit:
                break
        return out, ("ok" if out else "empty")
