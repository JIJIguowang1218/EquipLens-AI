# -*- coding: utf-8 -*-
"""死图床监测脚本测试（离线；不联网、不读生产路径）。"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

spec = importlib.util.spec_from_file_location(
    "monitor_bad_domains", ROOT / "scripts" / "monitor_bad_domains.py")
mon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mon)

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:200]))


def test_classify():
    assert mon.classify("http 403") == "http_403"
    assert mon.classify("http 404") == "http_404"
    assert mon.classify("NameResolutionError: getaddrinfo failed") == "dns"
    assert mon.classify("Exceeded 30 redirects") == "redirect"
    assert mon.classify("domain_blocked") == "blocked"
    assert mon.classify("") == "unknown"


def test_summarize_groups_by_host():
    rows = mon.summarize([
        {"host": "a.com", "error": "http 403", "run": "r1", "date": "2026-11-11", "url": "https://a.com/1.jpg"},
        {"host": "a.com", "error": "http 403", "run": "r2", "date": "2026-11-12", "url": "https://a.com/2.jpg"},
        {"host": "b.com", "error": "getaddrinfo failed", "run": "r1", "date": "2026-11-11", "url": "https://b.com/1.jpg"},
    ])
    assert rows[0]["host"] == "a.com" and rows[0]["total_failures"] == 2, rows
    assert rows[0]["runs"] == 2 and rows[0]["by_class"] == {"http_403": 2}, rows
    assert rows[0]["first_seen"] == "2026-11-11" and rows[0]["last_seen"] == "2026-11-12"
    assert rows[1]["by_class"] == {"dns": 1}, rows


def test_host_of():
    assert mon.host_of("https://IMG.jdzj.com:443/a.jpg") == "img.jdzj.com"
    assert mon.host_of("") == ""


if __name__ == "__main__":
    check("错误分类", test_classify)
    check("按域名聚合", test_summarize_groups_by_host)
    check("host 解析", test_host_of)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"bad_domains: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
