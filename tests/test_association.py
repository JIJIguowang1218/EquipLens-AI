# -*- coding: utf-8 -*-
"""关联分析 skill 的校验脚本测试：schema/规则/页槽/缓冲/库内盘点。"""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "skills" / "association" / "scripts"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import check_list  # noqa: E402
import inventory  # noqa: E402
import slots  # noqa: E402

SAMPLE = ROOT / "data-test" / "evals" / "sample-association-list-desert.json"
SCHEMA = ROOT / "skills" / "association" / "schemas" / "association-list.schema.json"

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:160]))


def _doc(**over):
    doc = json.loads(SAMPLE.read_text(encoding="utf-8"))
    doc.update(over)
    return doc


def test_sample_passes():
    doc = _doc()
    res = check_list.check(doc, json.loads(SCHEMA.read_text(encoding="utf-8")))
    assert res["ok"], res
    assert res["stats"]["recommended"] == 8, res["stats"]
    assert res["stats"]["slots_used"] == 12, res["stats"]
    assert res["stats"]["named_slots"] == 12, res["stats"]


def test_recommended_without_e3_fails():
    doc = _doc()
    doc["targets"][0]["evidence"] = []
    res = check_list.check(doc)
    assert not res["ok"], res
    assert any("E3" in e for e in res["errors"]), res["errors"]
    # 证据标题不含型号也不算
    doc = _doc()
    doc["targets"][0]["evidence"] = [{"url": "https://x.com/a", "title": "无关页面",
                                      "grade": "E3", "source": "corpus"}]
    res = check_list.check(doc)
    assert not res["ok"] and any("标题里没有该型号" in e for e in res["errors"]), res


def test_backup_with_slot_fails():
    doc = _doc()
    b = next(t for t in doc["targets"] if t["status"] == "backup")
    b["slots"] = ["vehicle:13"]
    res = check_list.check(doc)
    assert not res["ok"], res
    assert any("不得占槽" in e for e in res["errors"]), res["errors"]


def test_blocking_confirmation_with_recs_fails():
    doc = _doc()
    doc["needs_confirmation"].append(
        {"question": "口径确认", "why": "低置信档案", "blocking": True})
    res = check_list.check(doc)
    assert not res["ok"], res
    assert any("阻断" in e for e in res["errors"]), res["errors"]


def test_cross_vehicle_needs_flag():
    doc = _doc()
    doc["targets"][0]["relation"] = "cross_vehicle"
    res = check_list.check(doc)
    assert res["ok"], res
    assert any("cross_vehicle" in w for w in res["warnings"]), res["warnings"]
    doc["allow_cross_vehicle"] = True
    assert check_list.check(doc)["ok"], check_list.check(doc)


def test_page_overflow_fails():
    doc = _doc()
    doc["page_budget"]["vehicle_slots"] = 16
    res = check_list.check(doc)
    assert not res["ok"], res
    assert any("页数超限" in e for e in res["errors"]), res["errors"]


def test_empty_reason_warns():
    doc = _doc()
    doc["targets"][0]["reason"] = "与目标车型相似"
    res = check_list.check(doc)
    assert any("空话词" in w for w in res["warnings"]), res["warnings"]


def test_buffer_and_family_rules():
    assert slots.buffer_size(12) == 2
    assert slots.buffer_size(12, thin=True) == 3
    cands = [
        {"id": f"a{i}", "tier": 1, "confidence": 0.9, "family": "德龙"} for i in range(3)
    ] + [{"id": "b1", "tier": 1, "confidence": 0.8, "family": "重汽"},
         {"id": "b2", "tier": 1, "confidence": 0.8, "family": "重汽"},
         {"id": "b3", "tier": 1, "confidence": 0.8, "family": "重汽"},
         {"id": "c1", "tier": 2, "confidence": 0.5, "family": "越野"}]
    res = slots.allocate(cands, vehicle_slots=5, requested=4)
    assert res["slots_used"] == 4, res
    # 8 条：德龙第 3 台、重汽第 3 台被同族上限剔除 → 池剩 5，取 4，备选 1
    assert len(res["backup"]) == 1, res
    assert len(res["dropped"]) == 2, res["dropped"]
    # 备选不占槽
    for t in res["targets"]:
        if t.get("status") == "backup":
            assert not t.get("slots"), t


def test_inventory_on_empty_db():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "empty.db"
        import sqlite3
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE vehicles (id TEXT, brand TEXT, model_name TEXT)")
        conn.execute("CREATE TABLE assets (id TEXT, vehicle_id TEXT, kind TEXT, "
                     "confirm_status TEXT, view_angle TEXT, width INTEGER)")
        conn.commit()
        conn.close()
        res = inventory.inventory(db, ["德龙6X6"], 1200)
        assert res["library_status"] == "ok", res
        assert res["models"][0]["to_verify"] is True, res
        assert any("库为空" in w for w in res["warnings"]), res["warnings"]
    missing = inventory.inventory(Path("no-such.db"), ["X"])
    assert missing["library_status"] == "db_missing", missing
    assert any("to_verify" in w for w in missing["warnings"]), missing["warnings"]


def test_provisional_slot_rules():
    """provisional：必须有车型名 + 至少 E1 证据 + verify_by；weak 要写理由。"""
    doc = _doc()
    t = next(x for x in doc["targets"] if x["status"] == "provisional")
    assert check_list.check(doc)["ok"], check_list.check(doc)
    t.pop("verify_by")
    res = check_list.check(doc)
    assert res["ok"] and any("verify_by" in w for w in res["warnings"]), res
    t["verify_by"] = "conformation_check"
    t["evidence"] = []
    res = check_list.check(doc)
    assert not res["ok"] and any("E1" in e for e in res["errors"]), res
    t["evidence"] = [{"url": "https://x.com/q", "title": "某型号 参数页",
                      "grade": "E1", "source": "serp"}]
    t["weak_reason"] = ""
    res = check_list.check(doc)
    assert res["ok"] and any("weak_reason" in w for w in res["warnings"]), res


def test_slots_provisional_vs_model_name():
    cands = [
        {"id": "p1", "tier": 2, "confidence": 0.5, "grounding": "inference",
         "verified": False, "models": [], "status": "provisional",
         "verify_by": "roster_generation", "family": "A"},
        {"id": "m1", "tier": 1, "confidence": 0.9, "grounding": "inference",
         "verified": False, "models": ["某型号 6x6（待核）"], "family": "B"},
    ]
    res = slots.allocate(cands, vehicle_slots=12, requested=12)
    assert res["recommended"] == ["p1"], res
    assert res["held"][0]["id"] == "m1", res


def test_slots_hold_unverified_inference():
    """未验证的推断哪怕置信最高，也只能进备选。"""
    cands = [
        {"id": "i1", "tier": 1, "confidence": 0.99, "grounding": "inference",
         "verified": False, "models": ["X 级（待核）"], "family": "A"},
        {"id": "v1", "tier": 2, "confidence": 0.4, "grounding": "roster",
         "verified": True, "family": "B"},
    ]
    res = slots.allocate(cands, vehicle_slots=12, requested=12)
    assert res["recommended"] == ["v1"], res
    assert res["held"][0]["id"] == "i1", res
    assert res["shortfall"] == 11, res


if __name__ == "__main__":
    check("样例清单通过校验", test_sample_passes)
    check("推荐位必须有 E3 且标题含型号", test_recommended_without_e3_fails)
    check("备选不得占槽", test_backup_with_slot_fails)
    check("阻断确认项存在时不得有推荐", test_blocking_confirmation_with_recs_fails)
    check("跨车型需显式开关", test_cross_vehicle_needs_flag)
    check("页数超限报错", test_page_overflow_fails)
    check("空话理由告警", test_empty_reason_warns)
    check("缓冲与同族上限", test_buffer_and_family_rules)
    check("未验证推断只进备选", test_slots_hold_unverified_inference)
    check("provisional 占槽规则", test_provisional_slot_rules)
    check("provisional 与型号名分流", test_slots_provisional_vs_model_name)
    check("库内盘点（空库/缺库）", test_inventory_on_empty_db)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"association: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
