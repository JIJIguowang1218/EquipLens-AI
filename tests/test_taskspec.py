# -*- coding: utf-8 -*-
"""TaskSpec 规范化/校验单测（不调网络）。"""
import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens import taskspec  # noqa: E402

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        RESULTS.append((name, "FAIL", str(e)[:200]))


def base(**over):
    s = {
        "intent": "new_task", "class": "沙漠牵引车", "class_raw": "沙漠车",
        "class_aliases": [], "environment": "沙漠/油田", "configuration": "6×6",
        "quantity": {"primary": 10, "backup": None, "delta": None},
        "brands_include": [], "brands_exclude": [],
        "preferences": {"soft_brands": [], "brand_quota": None, "foreign_ratio": None,
                        "views": ["front"], "quality": [], "year": None, "tonnage": None, "price": None},
        "models_pinned": [], "models_provided": [], "parts": [],
        "constraints": {"exclude": [], "origin": None, "powertrain": None, "min_width": None},
        "scope": None, "delivery": None, "policy": {"hard": ["quantity"], "soft": []},
        "unknowns": [], "assumptions": [], "questions": [], "session_context_used": False,
    }
    s.update(over)
    return s


def test_config_normalized():
    s = taskspec.normalize(base())
    assert s["configuration"] == "6x6", s["configuration"]


def test_modify_delta():
    s = taskspec.normalize(base(intent="modify", quantity={"primary": 2, "backup": None, "delta": None}))
    assert s["quantity"]["delta"] == 2 and s["quantity"]["primary"] is None, s["quantity"]


def test_soft_field_in_hard_moves_to_soft():
    s = taskspec.normalize(base(policy={"hard": ["quantity", "views"], "soft": []}))
    assert "views" not in s["policy"]["hard"], s["policy"]
    assert "views" in s["policy"]["soft"], s["policy"]


def test_domestic_only_maps_to_origin():
    s = taskspec.normalize(base(policy={"hard": ["quantity", "domestic_only"], "soft": []}))
    assert "constraints.origin" in s["policy"]["hard"], s["policy"]
    assert s["constraints"]["origin"] == "domestic", s["constraints"]


def test_electric_only_maps_to_powertrain():
    s = taskspec.normalize(base(policy={"hard": ["electric_only"], "soft": []}))
    assert "constraints.powertrain" in s["policy"]["hard"], s["policy"]
    assert s["constraints"]["powertrain"] == "electric", s["constraints"]


def test_unknown_policy_degrades():
    s = taskspec.normalize(base(policy={"hard": ["road_legal"], "soft": []}))
    assert s["policy"]["hard"] == [], s["policy"]
    assert any(u["field"] == "road_legal" and u["severity"] == "informational" for u in s["unknowns"])


def test_parts_dedupe_against_exclude():
    s = taskspec.normalize(base(parts=["内饰", "前保险杠"],
                                constraints={"exclude": ["内饰"], "origin": None,
                                             "powertrain": None, "min_width": None}))
    assert s["parts"] == ["前保险杠"], s["parts"]


def test_brand_quota_valid():
    s = taskspec.normalize(base(preferences={"soft_brands": [], "brand_quota":
                                              {"brands": ["奔驰", "沃尔沃"], "min": 3, "of": 10},
                                              "foreign_ratio": None, "views": [], "quality": [],
                                              "year": None, "tonnage": None, "price": None}))
    assert s["preferences"]["brand_quota"] == {"brands": ["奔驰", "沃尔沃"], "min": 3, "of": 10}


def test_brand_quota_invalid():
    s = taskspec.normalize(base(preferences={"soft_brands": [], "brand_quota":
                                              {"brands": [], "min": 5, "of": 3},
                                              "foreign_ratio": None, "views": [], "quality": [],
                                              "year": None, "tonnage": None, "price": None}))
    assert s["preferences"]["brand_quota"] is None
    assert any(u["field"] == "brand_quota" for u in s["unknowns"])


def test_questions_capped():
    s = taskspec.normalize(base(
        unknowns=[{"field": "class", "text": "缺类目", "severity": "blocking", "proposal": ""}],
        questions=[{"id": "q1", "question": "?", "options": ["a"], "default": "a"},
                   {"id": "q2", "question": "?", "options": ["b"], "default": "b"}]))
    assert len(s["questions"]) == 1


def test_questions_dropped_without_blocking():
    s = taskspec.normalize(base(unknowns=[{"field": "x", "text": "", "severity": "defaultable"}],
                                questions=[{"id": "q1", "question": "?", "options": [], "default": ""}]))
    assert s["questions"] == []


def test_severity_normalized():
    s = taskspec.normalize(base(unknowns=[{"field": "x", "text": "", "severity": "weird"}]))
    assert s["unknowns"][0]["severity"] == "informational"


def test_alias_map_explicit_only():
    s = taskspec.normalize(base(**{"class": "沙漠车", "class_raw": "沙漠车"}))
    assert s["class"] == "沙漠车"
    s2 = taskspec.normalize(base(**{"class": "沙漠车", "class_raw": "沙漠车"}), alias_map={"沙漠车": "沙漠牵引车"})
    assert s2["class"] == "沙漠牵引车"
    assert "沙漠车" in s2["class_aliases"]


def test_to_brief():
    b = taskspec.to_brief(base())
    assert b["request"]["class"] == "沙漠牵引车"
    assert b["request"]["page_budget"]["vehicle_slots"] == 10
    assert b["request"]["configuration"] == "6x6"


def test_validate_clean():
    assert taskspec.validate(taskspec.normalize(base())) == []


def test_validate_catches_bad():
    s = taskspec.normalize(base())
    s["policy"]["hard"] = ["nonsense"]
    s["unknowns"].append({"field": "x", "text": "", "severity": "weird"})
    issues = taskspec.validate(s)
    assert any("policy.hard" in i for i in issues), issues
    assert any("severity" in i for i in issues), issues


def test_chinese_enums():
    s = taskspec.normalize(base(constraints={"exclude": [], "origin": "国产",
                                             "powertrain": "电动", "min_width": None}))
    assert s["constraints"]["origin"] == "domestic"
    assert s["constraints"]["powertrain"] == "electric"


def test_provided_without_model_dropped():
    s = taskspec.normalize(base(models_provided=[{"model": "", "image": True},
                                                 {"model": "X3000", "image": True}]))
    assert s["models_provided"] == [{"model": "X3000", "image": True}], s["models_provided"]


def test_apply_taskspec_overlay():
    from equiplens import briefing
    brief = {"request": {"class": "旧类目", "page_budget": {"vehicle_slots": 4}},
             "part_requirements": [{"part": "step", "label": "登车踏步"}]}
    spec = taskspec.normalize(base())
    out = briefing.apply_taskspec(brief, spec)
    assert out["request"]["class"] == "沙漠牵引车"
    assert out["request"]["page_budget"]["vehicle_slots"] == 10
    assert out["request"]["environment"]["value"] == "沙漠/油田"
    assert out["s0"] == {"mechanism": "taskspec", "version": "v0.4"}
    assert out["part_requirements"][0]["part"] == "step"      # 其它字段不被覆盖
    assert out["taskspec"] is spec


def test_generate_brief_with_taskspec():
    from equiplens import briefing
    payload = {"request": {"class": "沙漠牵引车", "base_platform": "6x6 底盘",
                           "configuration": "6x6"},
               "regions": [], "parts": [{"part": "step", "label": "登车踏步"}],
               "assumptions": [], "negative": []}

    def fake_chat(prompt, key, model):
        return {"payload": payload, "usage": {}, "model": model}

    spec = taskspec.normalize(base())
    out = briefing.generate_brief("沙漠牵引车 10 台", "sk-test", taskspec=spec,
                                  chat_fn=fake_chat)
    b = out["brief"]
    assert b["s0"]["mechanism"] == "taskspec"
    assert b["request"]["class"] == "沙漠牵引车"
    assert b["request"]["page_budget"]["vehicle_slots"] == 10
    assert out["taskspec"] is spec


def test_no_mutation():
    src = base()
    snapshot = copy.deepcopy(src)
    taskspec.normalize(src)
    assert src == snapshot


def test_to_brief_carries_brands_pins_constraints():
    s = taskspec.normalize(base(brands_include=["陕汽"], brands_exclude=["北奔"],
                                models_pinned=["X3000"],
                                constraints={"exclude": ["挂车"], "origin": None,
                                             "powertrain": None, "min_width": None}))
    req = taskspec.to_brief(s)["request"]
    assert req["brands_include"] == ["陕汽"], req
    assert req["brands_exclude"] == ["北奔"], req
    assert req["models_pinned"] == ["X3000"], req
    assert req["constraints"]["exclude"] == ["挂车"], req


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for name, fn in tests:
        check(name, fn)
    fails = [r for r in RESULTS if r[1] == "FAIL"]
    for name, status, err in RESULTS:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"taskspec: {len(RESULTS) - len(fails)}/{len(RESULTS)} 通过")
    sys.exit(1 if fails else 0)
