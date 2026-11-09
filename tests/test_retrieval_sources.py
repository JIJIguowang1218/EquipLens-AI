# -*- coding: utf-8 -*-
"""P2-W2 源路由测试：fallback / 熔断 / 缓存 / SearXNG 解析（全离线）。"""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens.retrieval_engine.sources import (SearchCache, SourceHealth,  # noqa: E402
                                               SourceRouter, SearxngSource)

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:160]))


def hit(url="https://x/a.jpg", title="德龙X3000 6x6 工程车"):
    return {"url": url, "title": title, "channel": "fake"}


def test_fallback_when_blocked():
    calls = []

    def bad(q, n, m):
        calls.append("360")
        return [], "blocked:Forbid spider access"

    def good(q, n, m):
        calls.append("searxng")
        return [hit()], "ok"

    with tempfile.TemporaryDirectory() as td:
        router = SourceRouter([("360", bad), ("searxng", good)],
                              SourceHealth(Path(td) / "h.json"),
                              SearchCache(Path(td) / "c.json"))
        hits, diag = router.search("q", 3, "德龙X3000")
        assert len(hits) == 1 and calls == ["360", "searxng"], (hits, calls)
        assert diag[0]["status"].startswith("blocked"), diag


def test_circuit_opens_after_repeated_block():
    calls = []

    def bad(q, n, m):
        calls.append(1)
        return [], "blocked:captcha"

    with tempfile.TemporaryDirectory() as td:
        health = SourceHealth(Path(td) / "h.json", failure_threshold=2,
                              cooldown_seconds=300)
        router = SourceRouter([("360", bad)], health)
        router.search("q", 3)
        router.search("q", 3)
        assert len(calls) == 2, calls
        hits, diag = router.search("q", 3)
        assert hits == [] and len(calls) == 2, (hits, calls)
        assert diag[0]["status"] == "circuit_open", diag


def test_cache_avoids_second_call():
    calls = []

    def good(q, n, m):
        calls.append(1)
        return [hit()], "ok"

    with tempfile.TemporaryDirectory() as td:
        router = SourceRouter([("360", good)],
                              SourceHealth(Path(td) / "h.json"),
                              SearchCache(Path(td) / "c.json"))
        first, _ = router.search("q", 3)
        second, diag = router.search("q", 3)
        assert first == second and len(calls) == 1, (first, second, calls)
        assert diag[0]["channel"] == "cache", diag


def test_first_success_stops():
    calls = []

    def good(q, n, m):
        calls.append("360")
        return [hit()], "ok"

    def should_not(q, n, m):
        calls.append("searxng")
        return [hit(url="https://x/b.jpg")], "ok"

    with tempfile.TemporaryDirectory() as td:
        router = SourceRouter([("360", good), ("searxng", should_not)],
                              SourceHealth(Path(td) / "h.json"))
        hits, _ = router.search("q", 3)
        assert len(hits) == 1 and calls == ["360"], (hits, calls)


def test_searxng_parses_results():
    class Resp:
        status_code = 200

        @staticmethod
        def json():
            return {"results": [
                {"img_src": "https://x/1.jpg", "title": "德龙X3000 6x6 工程车",
                 "width": 1600, "height": 900},
                {"img_src": "https://x/2.jpg", "title": "德龙X3000 前脸",
                 "width": 1280, "height": 720}]}

    import equiplens.retrieval_engine.sources as sources
    orig = sources.requests.get
    sources.requests.get = lambda *a, **k: Resp()
    try:
        hits, status = SearxngSource("http://localhost:8080")(
            "德龙X3000", 3, "德龙X3000")
        assert status == "ok" and len(hits) == 2, (status, hits)
        assert hits[0]["channel"] == "searxng", hits
        assert hits[0]["width"] == 1600, hits
    finally:
        sources.requests.get = orig


if __name__ == "__main__":
    check("被拦后回落下一源", test_fallback_when_blocked)
    check("连续被拦触发熔断", test_circuit_opens_after_repeated_block)
    check("缓存避免重复打源", test_cache_avoids_second_call)
    check("首源成功即停", test_first_success_stops)
    check("SearXNG JSON 解析", test_searxng_parses_results)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"retrieval_sources: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
