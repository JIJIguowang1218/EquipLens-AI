# -*- coding: utf-8 -*-
"""域名基准纯函数测试（离线）。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import domainbench  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:160]))


def test_classify():
    assert domainbench.classify_trust(0.06) == "high"
    assert domainbench.classify_trust(0.03) == "medium"
    assert domainbench.classify_trust(0.01) == "low"
    assert domainbench.classify_trust(0.001) == "none"


def test_summarize():
    pages = [
        {"url": "https://a.com/1", "title": "t1", "status": "saved",
         "body_chars": 1000, "a_chars": 80, "channel": "baidu"},
        {"url": "https://a.com/2", "title": "t2", "status": "fetch_failed",
         "body_chars": 0, "a_chars": 0, "channel": "baidu"},
        {"url": "https://a.com/3", "title": "t3", "status": "robots_denied",
         "body_chars": 0, "a_chars": 0, "channel": "baidu"},
        {"url": "https://a.com/4", "title": "t4", "status": "saved",
         "body_chars": 500, "a_chars": 0, "channel": "bing"},
    ]
    s = domainbench.summarize("a.com", pages)
    assert s["saved"] == 2 and s["body_chars"] == 1500 and s["a_chars"] == 80
    assert s["a_per_kchar"] == round(80 / 1500 * 1000, 2), s["a_per_kchar"]
    assert s["baidu_pages"] == 1 and s["baidu_a_share"] == 0.08
    assert s["trust_suggested"] == "high", s
    assert s["robots_denied"] == 1 and s["fetch_failed"] == 1
    assert s["channels"] == ["baidu", "bing"]


def test_proposals():
    registry = {"sources": [
        {"domain": "autohome.com.cn", "trust": "medium"},
        {"domain": "360che.com", "trust": "high"},
    ]}
    lb = [
        {"domain": "360che.com", "trust_suggested": "high", "a_share": 0.07,
         "a_per_kchar": 70, "saved": 2, "body_chars": 8000, "baidu_pages": 2},
        {"domain": "autohome.com.cn", "trust_suggested": "none", "a_share": 0.0,
         "a_per_kchar": 0, "saved": 3, "body_chars": 20000, "baidu_pages": 3},
        {"domain": "newgood.com", "trust_suggested": "high", "a_share": 0.06,
         "a_per_kchar": 60, "saved": 2, "body_chars": 8000, "baidu_pages": 2},
        {"domain": "newbad.com", "trust_suggested": "none", "a_share": 0.0,
         "a_per_kchar": 0, "saved": 1, "body_chars": 1000, "baidu_pages": 1},
    ]
    p = domainbench.build_proposals(lb, registry)
    assert any(x["domain"] == "newgood.com" for x in p["add"]), p
    assert any(x["domain"] == "autohome.com.cn" for x in p["demote"]), p
    assert len(p["promote"]) == 0, p  # 已是 high，无需晋升
    assert any(x["domain"] == "newbad.com" for x in p["keep"]), p


def test_render():
    meta = {"generated_at": "2026-10-30", "queries": 2, "pages": 4}
    rows = [{"domain": "a.com", "pages": 2, "saved": 2, "body_chars": 1000,
             "a_chars": 50, "a_per_kchar": 50, "trust_suggested": "high",
             "registry_trust": "新"}]
    txt = domainbench.render_report(rows, {"promote": [], "demote": [],
                                           "add": [], "keep": []}, meta)
    assert "域名基准与发现报告" in txt and "排行榜" in txt


if __name__ == "__main__":
    check("信任等级阈值", test_classify)
    check("单域名指标汇总", test_summarize)
    check("升降级建议", test_proposals)
    check("报告渲染", test_render)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"domainbench: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
