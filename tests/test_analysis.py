# -*- coding: utf-8 -*-
"""analysis 测试：契约校验 / 多视角合并 / 三词台账（全离线，不调 API）。"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import analysis  # noqa: E402

VOCAB = {
    "stability": ["稳重", "敦实"],
    "tough": ["硬朗", "刚直"],
    "modern": ["整面化", "参数化"],
}
TAX = {
    "grille": ["冲孔网板格栅", "横置多层格栅"],
    "bumper": ["整体式保险杠"],
    "side_guard": ["型钢侧防护栏"],
    "wheel_arch": ["一体式同色轮拱"],
    "step": ["两级固定踏板"],
}
SLOTS = ["grille", "bumper", "side_guard", "wheel_arch", "step"]
results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:160]))


def part(slot, term, visible="full", **kw):
    base = {"slot": slot, "term": term, "visible": visible, "bbox": [1, 2, 3, 4],
            "part_family": "sheet_metal", "family_reason": "板面连续",
            "form": "形态一句。", "cmf": {"material_class": "钢板", "finish": "漆面"},
            "intent": "支撑。"}
    base.update(kw)
    return base


def ok_data():
    return {
        "unit": {"slot": "front_face", "kind": "region",
                 "members": ["grille", "bumper"],
                 "gesture": "前脸竖直上收。",
                 "character_lines": ["饰条横贯至灯上缘。", "格栅竖线落至杠上沿。"],
                 "proportion": "接近 2:1 扁宽（估）。",
                 "cmf": "同色漆，格栅哑黑。",
                 "judgement": "横向分层压住体量。",
                 "style_tags": [
                     {"tag": "稳重", "cluster": "stability", "evidence": "横向饰条贯通"},
                     {"tag": "硬朗", "cluster": "tough", "evidence": "灯具方正"},
                     {"tag": "整面化", "cluster": "modern", "evidence": "杠罩同色连片"}]},
        "parts": [
            part("grille", "冲孔网板格栅"),
            part("bumper", "整体式保险杠"),
            part("side_guard", "型钢侧防护栏"),
            part("wheel_arch", "一体式同色轮拱"),
            part("step", "两级固定踏板"),
        ],
        "unplaced": [],
    }


def test_valid_passes():
    assert analysis.validate_analysis(ok_data(), [], VOCAB, TAX, SLOTS) == []


def test_duplicate_cluster_rejected():
    d = ok_data()
    d["unit"]["style_tags"][1] = {"tag": "敦实", "cluster": "stability",
                                  "evidence": "宽幅面"}
    errs = analysis.validate_analysis(d, [], VOCAB, TAX, SLOTS)
    assert any("同簇" in e for e in errs), errs


def test_word_outside_cluster_rejected():
    d = ok_data()
    d["unit"]["style_tags"][0]["tag"] = "凶悍"
    errs = analysis.validate_analysis(d, [], VOCAB, TAX, SLOTS)
    assert any("不在簇" in e for e in errs), errs


def test_used_word_rejected():
    errs = analysis.validate_analysis(ok_data(), ["稳重"], VOCAB, TAX, SLOTS)
    assert any("已用词" in e for e in errs), errs


def test_not_visible_must_be_empty():
    d = ok_data()
    d["parts"][4] = part("step", None, visible="not_visible")
    d["parts"][4]["form"] = "有描述"
    errs = analysis.validate_analysis(d, [], VOCAB, TAX, SLOTS)
    assert any("not_visible" in e for e in errs), errs


def test_term_must_hit_taxonomy():
    d = ok_data()
    d["parts"][0]["term"] = "我自己编的格栅"
    errs = analysis.validate_analysis(d, [], VOCAB, TAX, SLOTS)
    assert any("不在名词表" in e for e in errs), errs


def test_missing_slot_rejected():
    d = ok_data()
    d["parts"] = d["parts"][:4]
    errs = analysis.validate_analysis(d, [], VOCAB, TAX, SLOTS)
    assert any("缺部件 step" in e for e in errs), errs


def test_long_line_rejected():
    d = ok_data()
    d["unit"]["gesture"] = "这" * 41
    errs = analysis.validate_analysis(d, [], VOCAB, TAX, SLOTS)
    assert any("超 40 字" in e for e in errs), errs


def test_normalize_strips_not_visible_fields():
    d = ok_data()
    d["parts"][4] = part("step", "两级固定踏板", visible="not_visible")
    d["parts"][4]["cmf"] = {"material_class": "钢", "finish": "漆"}
    repairs = analysis.normalize_analysis(d)
    assert d["parts"][4]["cmf"] is None
    assert d["parts"][4]["term"] is None
    assert repairs


def test_merge_takes_better_view():
    primary = {"unit": {"kind": "region"}, "parts": [
        part("step", None, visible="not_visible", form=None, cmf=None, intent=None)]}
    secondary = {"parts": [part("step", "两级固定踏板", visible="full")]}
    merged = analysis.merge_views(primary, secondary, view_tag="side")
    step = merged["parts"][0]
    assert step["visible"] == "full"
    assert step["source_view"] == "side"


def test_merge_keeps_primary_when_equal():
    primary = {"unit": {"kind": "region"}, "parts": [part("step", "两级固定踏板")]}
    secondary = {"parts": [part("step", "两级固定踏板")]}
    merged = analysis.merge_views(primary, secondary, view_tag="side")
    assert merged["parts"][0].get("source_view") != "side"


def test_ledger_tracks_usage_and_balance():
    led = analysis.TagLedger(VOCAB)
    led.take(["稳重"])
    led.take(["硬朗", "整面化"])
    assert led.used == ["稳重", "硬朗", "整面化"]
    assert led.balance() == 0


def test_prompt_contains_used_words_and_terms():
    p = analysis.build_prompt("测试车", ["稳重"], ["grille"], VOCAB,
                              {"grille": {"label": "进气格栅",
                                          "terms": [{"name": "冲孔网板格栅",
                                                     "when": "大面积冲孔"}]}})
    assert "稳重" in p and "冲孔网板格栅" in p and "进气格栅" in p
    for leftover in ("{vehicle}", "{used}", "{vocab}", "{terms}", "{slots}"):
        assert leftover not in p, leftover


def test_parse_json_strips_fence():
    d = analysis.parse_json('```json\n{"a": 1}\n```')
    assert d == {"a": 1}


if __name__ == "__main__":
    check("合法输出通过", test_valid_passes)
    check("同簇三词拒绝", test_duplicate_cluster_rejected)
    check("词不在簇内拒绝", test_word_outside_cluster_rejected)
    check("已用词拒绝", test_used_word_rejected)
    check("不可见不得带描述", test_not_visible_must_be_empty)
    check("构型名须命中名词表", test_term_must_hit_taxonomy)
    check("缺部件拒绝", test_missing_slot_rejected)
    check("超长句拒绝", test_long_line_rejected)
    check("矛盾字段就地归一", test_normalize_strips_not_visible_fields)
    check("补证取更好视角", test_merge_takes_better_view)
    check("同视角不覆盖", test_merge_keeps_primary_when_equal)
    check("三词台账", test_ledger_tracks_usage_and_balance)
    check("prompt 含词表与名词表", test_prompt_contains_used_words_and_terms)
    check("JSON 去围栏", test_parse_json_strips_fence)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"analysis: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
