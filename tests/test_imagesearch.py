# -*- coding: utf-8 -*-
"""imagesearch 通道健康与相关性护栏测试（不联网，全部 monkeypatch）。"""

import json
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


def test_search_platforms_applies_relevance():
    o360, obaidu = imagesearch._search_360, imagesearch._search_baidu
    imagesearch._search_360 = lambda q, n: (
        [{"url": "https://x/1.jpg", "title": "德龙X3000 6x6 沙漠越野"}], "ok")
    imagesearch._search_baidu = lambda q, n: (
        [{"url": "https://x/2.jpg", "title": "梅西壁纸"},
         {"url": "https://x/3.jpg", "title": "德龙X3000 6x6 实拍"}], "ok")
    try:
        hits, diag = imagesearch.search_platforms("德龙X3000 6x6 沙漠", 6, model="德龙X3000 6x6")
        assert [h["url"] for h in hits] == ["https://x/1.jpg", "https://x/3.jpg"], hits
        assert diag[1]["filtered"] == 1, diag
    finally:
        imagesearch._search_360, imagesearch._search_baidu = o360, obaidu


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


def test_360_uses_original_image():
    """360 的 thumb 是缩略图；应优先取 img 原图，并带尺寸/通道/referer。"""
    class Resp:
        status_code = 200
        text = json.dumps({"list": [{
            "img": "http://x/full.jpg", "thumb": "http://x/thumb.jpg",
            "title": "测试", "width": 1600, "height": 900}]})

    orig = imagesearch.requests.get
    imagesearch.requests.get = lambda *a, **k: Resp()
    try:
        hits, status = imagesearch._search_360("测试", 5)
        assert status == "ok", status
        assert hits[0]["url"] == "http://x/full.jpg", hits
        assert hits[0]["width"] == 1600 and hits[0]["height"] == 900, hits
        assert hits[0]["channel"] == "360", hits
        assert hits[0]["referer"] == "https://image.so.com/", hits
    finally:
        imagesearch.requests.get = orig


def test_hd_ladder_prefers_high_res():
    o360, obaidu, obing = (imagesearch._search_360, imagesearch._search_baidu,
                           imagesearch._search_bing)
    calls = []

    def fake360(q, n):
        calls.append(q)
        width = 1600 if ("高清" in q or "大图" in q) else 600
        return ([{"url": f"https://x/{len(calls)}.jpg", "thumb_url": "",
                  "title": "德龙X3000 6x6 工程车", "width": width,
                  "height": 900, "channel": "360",
                  "referer": "https://image.so.com/"}], "ok")

    imagesearch._search_360 = fake360
    imagesearch._search_baidu = lambda q, n: ([], "empty")
    imagesearch._search_bing = lambda q, n: ([], "empty")
    try:
        hits, diag = imagesearch.search_images_hd(
            "德龙X3000 侧视", 3, model="德龙X3000", hd=True)
        assert hits and hits[0]["width"] == 1600, hits
        assert any("高清" in q for q in calls), calls
        assert any("大图" in q for q in calls), calls
    finally:
        (imagesearch._search_360, imagesearch._search_baidu,
         imagesearch._search_bing) = o360, obaidu, obing


def test_upgrade_image_url():
    """CDN 缩放后缀升大图：只认纯数字后缀，已 ≥1200 与非数字后缀不动。"""
    up = imagesearch.upgrade_image_url
    assert up("https://img4.kcimg.cn/imgc/0/865/865416.jpg!600") ==         "https://img4.kcimg.cn/imgc/0/865/865416.jpg!1200"
    assert up("http://imgh.360che.com/imgc/0/228/228802.jpg!360") ==         "http://imgh.360che.com/imgc/0/228/228802.jpg!1200"
    assert up("https://a.com/x.jpg!1200") is None
    assert up("https://a.com/x.jpg!news.pc") is None
    assert up("https://a.com/x.jpg") is None
    assert up("") is None


def test_extract_page_images():
    """图集页抽图：绝对化、去小图标、按后缀去重、尊重 limit。"""
    html = """
    <img src="/a/1.jpg!600"><img data-src="https://x.com/a/1.jpg!800">
    <img src="https://x.com/a/2.jpg"><img src="https://x.com/logo.png">
    <img src="https://x.com/a/3.jpg"><img src="https://x.com/a/4.jpg">
    """
    got = imagesearch.extract_page_images(html, "https://x.com/news/1.html", limit=3)
    assert got == ["https://x.com/a/1.jpg!600", "https://x.com/a/2.jpg",
                   "https://x.com/a/3.jpg"], got
    assert imagesearch.upgrade_image_url("https://x.com/a/1.jpg!600") ==         "https://x.com/a/1.jpg!1200"


def test_download_candidates():
    """下载候选：大图后缀 → 原 URL → 去后缀裸图。"""
    c = imagesearch.download_candidates("https://x.com/a.jpg!600")
    assert c[0].endswith("a.jpg!1200"), c
    assert c[1].endswith("a.jpg!600"), c
    assert c[2].endswith("a.jpg"), c
    c = imagesearch.download_candidates("https://x.com/a.jpg")
    assert c == ["https://x.com/a.jpg"], c


def test_upgrade_sohu_url():
    """搜狐图床 w_640 → w_1280（实测 640x426 → 1280x852）。"""
    up = imagesearch.upgrade_image_url
    u = "http://5b0988e595225.cdn.sohucs.com/q_70,c_zoom,w_640/images/2019/a.jpeg"
    assert up(u) == u.replace("w_640", "w_1280"), up(u)
    assert up(u.replace("w_640", "w_1280")) is None


def test_domain_health_blocks_after_threshold():
    """连续 N 次 403/DNS 后拉黑该 host，不再浪费下载尝试。"""
    h = imagesearch.DomainHealth(threshold=3)
    for i in range(3):
        h.record(f"https://dead.example/{i}.jpg", "http 403")
    assert h.is_blocked("https://dead.example/x.jpg")
    out = imagesearch._download_and_gate(
        {"url": "https://dead.example/x.jpg", "title": "t"}, health=h)
    assert out["error"] == "domain_blocked" and out["tries"] == 0, out
    # 软错误（如图片过小）不计入拉黑
    h2 = imagesearch.DomainHealth(threshold=2)
    h2.record("https://ok.example/a.jpg", "图片过小")
    assert not h2.is_blocked("https://ok.example/b.jpg")


if __name__ == "__main__":
    check("相关性护栏", test_relevance_guard)
    check("构型/品牌/非车污染护栏", test_config_and_brand_guard)
    check("整车主图外观策略", test_exterior_policy)
    check("多通道累加 + 标注通道", test_search_accumulates_and_marks_channel)
    check("平台组合：相关性预筛", test_search_platforms_applies_relevance)
    check("不相关通道自动跳过", test_unrelated_channel_falls_through)
    check("被拦状态如实上报", test_blocked_status_reported)
    check("360 取原图而非缩略图", test_360_uses_original_image)
    check("高清/大图阶梯优先高清", test_hd_ladder_prefers_high_res)
    check("CDN 后缀升大图", test_upgrade_image_url)
    check("下载候选阶梯", test_download_candidates)
    check("图集页抽图", test_extract_page_images)
    check("搜狐 w_1280 升图", test_upgrade_sohu_url)
    check("死图床拉黑", test_domain_health_blocks_after_threshold)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"imagesearch: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
