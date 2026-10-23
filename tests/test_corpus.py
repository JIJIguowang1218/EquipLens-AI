"""corpus 测试: 采集计划校验 / SERP 锚点抽取 / 语料落盘 / 结算（全离线, 无网络）。

运行: python tests/test_corpus.py
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import corpus  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:120]))


# ---------- build_plan ----------

def test_plan_defaults():
    p = corpus.build_plan({"review": ["q1"], "official": ["q2"]})
    assert p["quota"] == {"official": 3, "review": 4}, p["quota"]
    assert p["queries"]["review"] == ["q1"]
    assert p["batch_id"].startswith("batch-corpus-")


def test_plan_quota_override_and_unknown_type():
    p = corpus.build_plan({"spec": ["q"]}, quota={"spec": 5}, batch_id="b1")
    assert p["quota"]["spec"] == 5 and p["batch_id"] == "b1"
    try:
        corpus.build_plan({"bad_type": ["q"]})
        raise AssertionError("应当拒绝未知信源类型")
    except ValueError:
        pass


# ---------- pick_anchors ----------

SERP_MD = """
### 百度结果
[汕德卡C9H试驾：重卡外观设计评析](https://www.360che.com/review/123.html)
[中国重汽官网-汕德卡](https://www.sinotruk.com/vehicle/c9h)
[百度白皮书_百度百科](https://baike.baidu.com/item/x)
[点击搜索更多](https://www.baidu.com/s?wd=next)
[某视频-汕德卡](https://v.baidu.com/123)
[汕德卡C9H试驾：重卡外观设计评析](https://www.360che.com/review/123.html)
[汽车报价低至3折](https://ad.example.com/promo)
[解放J7冬季使用手册.PDF](https://www.360che.com/manual.pdf)
[汕德卡C9H 收藏](https://www.360che.com/fav/1)
"""


def test_pick_anchors_filters_and_dedup():
    got = corpus.pick_anchors(SERP_MD, max_n=10)
    urls = [a["url"] for a in got]
    # baidu 自有域 / 站内搜索 / 视频 / PDF / 广告无关站 / 短标题 全部过滤
    assert urls == ["https://www.360che.com/review/123.html"], urls


def test_pick_anchors_exclude_and_cap():
    seen = {"https://www.360che.com/review/123.html"}
    md = SERP_MD + "\n[豪沃TH7评测：重卡](https://www.d1cm.com/a/9.html)"
    got = corpus.pick_anchors(md, max_n=5, exclude=seen)
    assert [a["url"] for a in got] == ["https://www.d1cm.com/a/9.html"]
    assert corpus.pick_anchors(SERP_MD, max_n=0) == []


# ---------- slugify / write_doc / summarize ----------

def test_slugify():
    assert corpus.slugify("汕德卡C9H试驾 评测!", "https://x.com/a") == "汕德卡C9H试驾评测"
    h = corpus.slugify("!!", "https://x.com/abc")
    assert len(h) == 12 and h.isalnum()


def test_serp_blocked_and_bing():
    assert corpus.serp_looks_blocked("")
    assert corpus.serp_looks_blocked("百度安全验证，输入验证码")
    assert corpus.serp_looks_blocked("没有与此相关的结果")
    assert not corpus.serp_looks_blocked("高空作业车外观设计全文" * 20)
    url = corpus._bing_serp_url("高空作业车 造型")
    assert url.startswith("https://www.bing.com/search?q=") and "format=rss" in url
    rss = ("<rss><channel>"
           "<item><title><![CDATA[高空作业车造型解读]]></title>"
           "<link><![CDATA[https://www.360che.com/a.html]]></link></item>"
           "<item><title>百度百科</title><link>https://baike.baidu.com/x</link></item>"
           "</channel></rss>")
    md = corpus._parse_bing_rss(rss)
    assert "[高空作业车造型解读](https://www.360che.com/a.html)" in md
    assert "[百度百科](https://baike.baidu.com/x)" in md


def test_write_doc_and_summarize():
    tmp = Path(tempfile.mkdtemp())
    try:
        doc = {"url": "https://a.com/1", "source_type": "review", "query": "q",
               "title": "测试文章标题", "fetched_at": "2026-10-22T10:00:00",
               "robots": "allow"}
        p = corpus.write_doc(tmp, 3, doc, "正文内容")
        text = p.read_text(encoding="utf-8")
        assert text.startswith("---\n") and "chars: 4" in text
        assert "source_type: review" in text and "正文内容" in text
        assert p.name == "003-测试文章标题.md"
        index = [{"source_type": "review", "status": "saved"},
                 {"source_type": "review", "status": "too_short"},
                 {"source_type": "spec", "status": "saved"}]
        s = corpus.summarize(index)
        assert s["review"] == {"saved": 1, "failed": 1}
        assert s["spec"] == {"saved": 1, "failed": 0}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    check("计划默认配额与归档", test_plan_defaults)
    check("计划配额覆盖与未知类型拒绝", test_plan_quota_override_and_unknown_type)
    check("锚点抽取过滤与去重", test_pick_anchors_filters_and_dedup)
    check("锚点排除与上限", test_pick_anchors_exclude_and_cap)
    check("slug 生成", test_slugify)
    check("SERP 被拦识别与 Bing RSS 解析", test_serp_blocked_and_bing)
    check("语料落盘与结算", test_write_doc_and_summarize)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"corpus: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
