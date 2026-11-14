# -*- coding: utf-8 -*-
"""任务单生成测试（不联网；LLM 用假响应）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens import briefing  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:200]))


def payload():
    return {
        "request": {"class": "沙漠牵引车", "environment": "沙漠/油田工况",
                    "base_platform": "6×6 重型卡车底盘", "configuration": "6×6"},
        "regions": [{"region": "front_face", "label": "前脸",
                     "views": ["front", "hero_45"], "accept": "C"}],
        "parts": [
            {"part": "step", "label": "登车踏步", "location": "side_lower",
             "design_relevance": "strong", "accept": "B",
             "design_axes": ["structure", "function_ergonomics", "environment_protection"],
             "views": ["side", "hero_45"], "mechanism": ["防滑", "沙尘"]},
            {"part": "headlamp", "label": "大灯", "location": "front",
             "design_relevance": "conditional", "accept": "A",
             "views": ["front", "hero_45"], "mechanism": ["沙尘"]},
        ],
        "assumptions": [{"field": "environment", "value": "沙漠/油田工况",
                         "why": "用户提到沙漠牵引车", "confidence": 0.8}],
        "negative": ["客车"],
    }


def test_assemble_brief():
    b = briefing.assemble_brief(payload(), "沙漠牵引车，看踏步和大灯", slots=12)
    assert b["request"]["class"] == "沙漠牵引车", b
    assert b["request"]["page_budget"]["vehicle_slots"] == 12, b
    assert [u["quota"] for u in b["research_units"]] == [8, 4], b["research_units"]
    assert b["tiers"] == ["exact", "environment"], b
    assert [p["part"] for p in b["part_requirements"]] == ["step", "headlamp"], b
    assert b["region_requirements"][0]["region"] == "front_face", b
    assert "gesture" in b["region_requirements"][0]["fields"], b
    assert b["part_requirements"][0]["label"] == "登车踏步", b
    assert "客车" in b["negative"] and "SUV" in b["negative"], b["negative"]
    assert briefing.validate_brief_json(b) == [], briefing.validate_brief_json(b)
    from equiplens.retrieval_engine.contracts import Brief
    rb = Brief.from_dict(b)
    assert rb.parts_by_key["step"].design_axes == ("structure", "function_ergonomics", "environment_protection"), rb


def test_single_slot():
    b = briefing.assemble_brief(payload(), "只做一台", slots=1)
    assert len(b["research_units"]) == 1 and b["research_units"][0]["quota"] == 1, b
    assert b["tiers"] == ["exact"], b


def test_unknown_part_kept():
    """词表外的新部件不能被拒；保留原词并标 custom/new。"""
    p = payload()
    p["parts"] = [{"part": "涉水喉", "label": "涉水喉", "location": "side_cab_rear",
                   "views": ["side"], "design_axes": ["function_ergonomics"]}]
    b = briefing.assemble_brief(p, "沙漠牵引车，加涉水喉", slots=12)
    part = b["part_requirements"][0]
    assert part["part"].startswith("custom_"), part
    assert "涉水喉" in part["part"], part          # key 可读，不是 sha1 哈希
    assert part["label"] == "涉水喉", part
    assert part["taxonomy_status"] == "new", part
    assert part["design_axes"] == ["function_ergonomics"], part
    assert any("parts.new" == a.get("field") for a in b["assumptions"]), b["assumptions"]


def test_missing_class_rejected():
    p = payload()
    p["request"] = {"environment": "沙漠"}
    try:
        briefing.assemble_brief(p, "沙漠车", slots=12)
    except ValueError as e:
        assert "class" in str(e), e
    else:
        raise AssertionError("应拒绝缺 class")


def test_generate_uses_llm_prompt():
    seen = {}

    def fake_chat(prompt, key, model):
        seen["prompt"] = prompt
        seen["key"] = key
        return {"payload": payload(), "usage": {}, "model": model}

    out = briefing.generate_brief("沙漠牵引车，看踏步和大灯", "sk-test",
                                  slots=12, chat_fn=fake_chat)
    assert seen["key"] == "sk-test", seen
    assert "no_vocabulary_note" in seen["prompt"] and "task-brief" in seen["prompt"], seen
    assert out["brief"]["brief_id"].startswith("auto-"), out["brief"]
    assert out["attempts"] == 1, out


if __name__ == "__main__":
    check("LLM 输出 → 完整 brief", test_assemble_brief)
    check("单槽规则", test_single_slot)
    check("词表外部件保留", test_unknown_part_kept)
    check("缺 class 拒绝", test_missing_class_rejected)
    check("generate 调 LLM 并带 skill", test_generate_uses_llm_prompt)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"briefing: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
