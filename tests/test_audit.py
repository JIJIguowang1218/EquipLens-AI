# -*- coding: utf-8 -*-
"""误杀抽样检测测试（离线，合成批次）。"""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import audit  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:160]))


BODY = """前脸采用V字形格栅，线条硬朗，镀铬饰条贯穿，营造出强烈的力量感与家族化识别。
2022款 2.0T柴油商运版长轴高顶厢货2座D20TCIF1
该车造型设计前脸大灯，马力620，油耗25，报价40万
全系标配ABS
"""


def _make_batch(td: Path) -> Path:
    b = td / "batch-audit"
    b.mkdir()
    (b / "001-doc.md").write_text("---\nurl: x\n---\n\n" + BODY, encoding="utf-8")
    (b / "index.json").write_text(json.dumps({"index": [
        {"status": "saved", "url": "https://www.autohome.com.cn/x", "title": "测试",
         "file": "001-doc.md", "source_type": "review"}]}), encoding="utf-8")
    return b


def test_collect_only_c():
    with tempfile.TemporaryDirectory() as td:
        b = _make_batch(Path(td))
        rows = audit.collect_c_passages(b, {"sources": []})
        assert rows, "应收集到 C 档段落"
        from equiplens import passage
        for r in rows:
            assert passage.score_passage(r["text"], "medium")["label"] == "C", r


def test_sheet_strata_and_guard():
    with tempfile.TemporaryDirectory() as td:
        b = _make_batch(Path(td))
        rows = audit.collect_c_passages(b, {"sources": []})
        sheet = audit.build_sheet(rows, sample_per_stratum=2)
        assert sheet["population"] == len(rows)
        assert sheet["strata"]
        total_sampled = sum(len(s["samples"]) for s in sheet["strata"])
        assert 1 <= total_sampled <= len(rows), total_sampled
        assert sheet["guard_count"] >= 1, sheet["guard_count"]  # 强语汇 C 进队列
        assert any("前脸" in g["text"] for g in sheet["guard_queue"])


def test_apply_weighted_miss_rate():
    with tempfile.TemporaryDirectory() as td:
        b = _make_batch(Path(td))
        rows = audit.collect_c_passages(b, {"sources": []})
        sheet = audit.build_sheet(rows, sample_per_stratum=2)
        first = sheet["strata"][0]["samples"][0]
        verdicts = {first["id"]: "P"}  # 判一条为漏杀
        res = audit.apply_verdicts(sheet, verdicts)
        assert 0 < res["estimated_miss_rate"] <= 1, res
        assert res["judged"] == sum(len(s["samples"]) for s in sheet["strata"])
        txt = audit.render_report(res)
        assert "估计漏杀率" in txt and "分层明细" in txt


if __name__ == "__main__":
    check("C 档收集（只含 C）", test_collect_only_c)
    check("分层抽样与护栏队列", test_sheet_strata_and_guard)
    check("加权漏杀率估计与报告", test_apply_weighted_miss_rate)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"audit: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
