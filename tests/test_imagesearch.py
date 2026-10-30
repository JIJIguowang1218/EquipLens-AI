# -*- coding: utf-8 -*-
"""imagesearch 通道健康与相关性护栏测试（不联网，全部 monkeypatch）。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import gate, imagesearch  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:160]))


def test_relevance_guard():
    q = "德龙X3000 6x6 沙漠牵引车"
    assert imagesearch._relevant(q, "惊现陕汽德龙X3000 6x6沙漠越野车")
    assert not imagesearch._relevant(q, "梅西壁纸 高清")
    assert not imagesearch._relevant(q, "")


def test_exterior_policy():
    """整车主图 = 门卫放行 + 外观视角；部件特写/内饰不得当主图。"""
    og, ov = gate.check, gate.classify_view
    gate.check = lambda d, t=0.0: {"pass": True, "margin": 0.1}
    gate.classify_view = lambda d: {"view": "interior", "score": 0.4}
    try:
        r = gate.check_exterior(b"x")
        assert r["pass"] and not r["exterior"] and r["reason"] == "not_exterior:interior", r
        gate.classify_view = lambda d: {"view": "detail", "score": 0.4}
        assert not gate.check_exterior(b"x")["exterior"]
        gate.classify_view = lambda d: {"view": "hero_45", "score": 0.4}
        r = gate.check_exterior(b"x")
        assert r["exterior"] and r["reason"] == "ok", r
        gate.check = lambda d, t=0.0: {"pass": False, "margin": -0.1}
        r = gate.check_exterior(b"x")
        assert not r["exterior"] and r["reason"] == "gate_drop", r
    finally:
        gate.check, gate.classify_view = og, ov


def test_config_and_brand_guard():
    m = "北奔 NG80 6X6"
    assert imagesearch._relevant("x", "北奔NG80 6x6军用卡车", m)
    assert not imagesearch._relevant("x", "北奔 NG80重卡 6X2 牵引车", m)  # 构型不符
    assert not imagesearch._relevant("x", "斯堪尼亚XT 6x6 工程车", m)     # 品牌不符
    assert not imagesearch._relevant("x", "解放战争历史纪录片", "解放 6x6")  # 非车污染


def test_search_accumulates_and_marks_channel():
    orig = imagesearch._search_360
    imagesearch._search_360 = lambda q, n: (
        [{"url": "https://x/1.jpg", "thumb_url": "", "title": "德龙X3000 6x6 沙漠越野"}], "ok")
    try:
        hits, diag = imagesearch.search_images_ex("德龙X3000 6x6 沙漠", 3)
        assert hits and hits[0]["channel"] == "360", hits
        assert diag[0]["channel"] == "360" and diag[0]["relevant"] == 1, diag
    finally:
        imagesearch._search_360 = orig


def test_unrelated_channel_falls_through():
    o360, obaidu = imagesearch._search_360, imagesearch._search_baidu
    imagesearch._search_360 = lambda q, n: (
        [{"url": "https://x/a.jpg", "thumb_url": "", "title": "梅西壁纸"}], "ok")
    imagesearch._search_baidu = lambda q, n: (
        [{"url": "https://x/b.jpg", "thumb_url": "", "title": "德龙X3000 沙漠牵引车实拍"}], "ok")
    try:
        hits, diag = imagesearch.search_images_ex("德龙X3000 沙漠", 3)
        assert len(hits) == 1 and hits[0]["channel"] == "baidu", hits
        assert diag[0]["relevant"] == 0, diag
    finally:
        imagesearch._search_360, imagesearch._search_baidu = o360, obaidu


def test_blocked_status_reported():
    o360, obaidu, obing = (imagesearch._search_360, imagesearch._search_baidu,
                           imagesearch._search_bing)
    imagesearch._search_360 = lambda q, n: ([], "blocked:Forbid spider access")
    imagesearch._search_baidu = lambda q, n: ([], "blocked:antiFlag")
    imagesearch._search_bing = lambda q, n: ([], "empty")
    try:
        hits, diag = imagesearch.search_images_ex("德龙X3000", 3)
        assert hits == [], hits
        assert diag[0]["status"].startswith("blocked"), diag
    finally:
        (imagesearch._search_360, imagesearch._search_baidu,
         imagesearch._search_bing) = o360, obaidu, obing


if __name__ == "__main__":
    check("相关性护栏", test_relevance_guard)
    check("构型/品牌/非车污染护栏", test_config_and_brand_guard)
    check("整车主图外观策略", test_exterior_policy)
    check("多通道累加 + 标注通道", test_search_accumulates_and_marks_channel)
    check("不相关通道自动跳过", test_unrelated_channel_falls_through)
    check("被拦状态如实上报", test_blocked_status_reported)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"imagesearch: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
