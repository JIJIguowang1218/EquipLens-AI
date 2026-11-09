# -*- coding: utf-8 -*-
"""检索中引擎 P1 测试：契约/库内优先/外检/降级/缺口/续跑/事件（全离线）。"""

import copy
import json
import sys
import tempfile
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens.retrieval_engine import (Asset, Brief, PartRequirement,  # noqa: E402
                                       RetrievalEngine, RunStore, validate_brief)
from equiplens.retrieval_engine.adapters import FakeWorld  # noqa: E402
from equiplens.retrieval_engine.evidence import EvidenceStore  # noqa: E402
from equiplens.retrieval_engine.web import (NullLibraryAdapter,  # noqa: E402
                                            RuleVerifier, WebWorld)

FIX = ROOT / "data-test" / "retrieval-fixtures-20261109"

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:200]))


def base_brief(parts=("bumper", "step"), units=None, tiers=("exact", "environment"),
               slots=1):
    return {
        "brief_id": "b-test",
        "request": {"class": "沙漠牵引车",
                    "page_budget": {"vehicle_slots": slots}},
        "part_requirements": [
            {"part": p, "label": p, "location": "x", "design_relevance": "strong",
             "views": ["front"], "accept": "A", "mechanism": []}
            for p in parts
        ],
        "research_units": units or [{
            "unit_id": "u-exact", "tier": "exact", "scope": "沙漠牵引车",
            "parts": list(parts), "quota": 1,
            "budget": {"max_queries": 6}, "stop": "",
        }],
        "tiers": list(tiers),
        "budget": {"max_queries": 10},
        "stop_rules": {},
        "negative": [],
        "strategy_ref": "default@v1",
    }


def target(tid, parts):
    return {"target_id": tid, "model": tid, "parts": list(parts)}


def asset(aid, view="front"):
    return {"asset_id": aid, "view": view, "width": 1600, "height": 900}


def ok(grade="E2"):
    return {"accepted": True, "identity": "confirmed", "visibility": "full",
            "origin": "oem", "grade": grade, "defects": []}


def bad(defect="wrong_identity"):
    return {"accepted": False, "identity": "unknown", "visibility": "full",
            "origin": "unknown", "grade": "", "defects": [defect]}


def one_unit_world(*, lib=None, ext=None, verify=None):
    return {"library": lib or {}, "external": ext or {},
            "assets": {}, "verify": verify or {}}


def run_engine(brief_data, world_data, run_id="t1", root=None):
    errors = validate_brief(brief_data)
    assert not errors, errors
    brief = Brief.from_dict(brief_data)
    world = FakeWorld(world_data)
    engine = RetrievalEngine(brief, world, run_root=root, run_id=run_id)
    return engine.run(), world


def test_brief_validation():
    data = json.loads((FIX / "brief-desert.json").read_text(encoding="utf-8"))
    assert validate_brief(data) == [], validate_brief(data)
    broken = copy.deepcopy(data)
    broken["part_requirements"] = []
    assert "part_requirements 不能为空" in validate_brief(broken)


def test_library_first_no_external():
    b = base_brief()
    w = {
        "library": {"u-exact": [target("lib-1", ["bumper", "step"])]},
        "external": {"u-exact": [target("ext-1", ["bumper", "step"])]},
        "assets": {
            "lib-1": {"bumper": [asset("lib-1-bumper")], "step": [asset("lib-1-step")]},
            "ext-1": {"bumper": [asset("ext-1-bumper")], "step": [asset("ext-1-step")]},
        },
        "verify": {k: ok() for k in
                   ["lib-1-bumper", "lib-1-step", "ext-1-bumper", "ext-1-step"]},
    }
    with tempfile.TemporaryDirectory() as td:
        summary, world = run_engine(b, w, root=td)
        assert summary["state"] == "DONE", summary
        assert summary["coverage"]["u-exact"]["accepted"] == 1, summary
        assert world.calls["external"] == 0, world.calls
        assert world.calls["library"] == 1, world.calls


def test_external_fallback_after_library_reject():
    b = base_brief()
    w = {
        "library": {"u-exact": [target("lib-1", ["bumper", "step"])]},
        "external": {"u-exact": [target("ext-1", ["bumper", "step"])]},
        "assets": {
            "lib-1": {"bumper": [asset("lib-1-bumper")], "step": [asset("lib-1-step")]},
            "ext-1": {"bumper": [asset("ext-1-bumper")], "step": [asset("ext-1-step")]},
        },
        "verify": {
            "lib-1-bumper": ok(), "lib-1-step": bad(),
            "ext-1-bumper": ok(), "ext-1-step": ok(),
        },
    }
    with tempfile.TemporaryDirectory() as td:
        summary, world = run_engine(b, w, root=td)
        assert summary["state"] == "DONE", summary
        assert summary["accepted_targets"]["u-exact"] == ["ext-1"], summary
        assert world.calls["external"] == 1, world.calls


def test_degrade_to_next_tier():
    b = base_brief()
    w = {
        "library": {},
        "external": {
            "u-exact": [target("ext-bad", ["bumper", "step"])],
            "u-environment": [target("ext-good", ["bumper", "step"])],
        },
        "assets": {
            "ext-bad": {"bumper": [asset("bad-bumper")], "step": [asset("bad-step")]},
            "ext-good": {"bumper": [asset("good-bumper")], "step": [asset("good-step")]},
        },
        "verify": {
            "bad-bumper": bad(), "bad-step": bad(),
            "good-bumper": ok(), "good-step": ok(),
        },
    }
    # 第二个 unit 用 environment tier；引擎按 tiers 顺序开层
    b["research_units"].append({
        "unit_id": "u-environment", "tier": "environment",
        "scope": "沙漠环境用车", "parts": ["bumper", "step"], "quota": 1,
        "budget": {"max_queries": 6}, "stop": "",
    })
    with tempfile.TemporaryDirectory() as td:
        summary, world = run_engine(b, w, root=td)
        assert summary["state"] == "DONE", summary
        actions = [d["action"] for d in summary["decisions"]]
        assert "open_next_tier" in actions, actions
        assert summary["accepted_targets"]["u-environment"] == ["ext-good"], summary


def test_gap_report_when_all_fail():
    b = base_brief()
    w = {"library": {}, "external": {}, "assets": {}, "verify": {}}
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        assert summary["state"] == "FAILED", summary
        assert summary["gaps"] == ["u-exact"], summary
        actions = [d["action"] for d in summary["decisions"]]
        assert "all_tiers_exhausted" in actions, actions


def test_resume_skips_finished_run():
    b = base_brief()
    w = {
        "library": {"u-exact": [target("lib-1", ["bumper", "step"])]},
        "assets": {
            "lib-1": {"bumper": [asset("lib-1-bumper")], "step": [asset("lib-1-step")]},
        },
        "verify": {"lib-1-bumper": ok(), "lib-1-step": ok()},
    }

    class ExplodingWorld:
        def library_targets(self, unit):
            raise AssertionError("resume 后不应再调库")

        def external_targets(self, unit):
            raise AssertionError("resume 后不应再外检")

        def fetch(self, target, part):
            raise AssertionError("resume 后不应再抓取")

        def verify(self, asset, part):
            raise AssertionError("resume 后不应再核验")

    with tempfile.TemporaryDirectory() as td:
        first, _ = run_engine(b, w, root=td)
        assert first["state"] == "DONE", first
        brief = Brief.from_dict(b)
        second = RetrievalEngine(brief, ExplodingWorld(), run_root=td,
                                 run_id="t1").run()
        assert second["state"] == "DONE", second


def test_idempotent_asset_dedupe():
    b = base_brief()
    w = {
        "library": {"u-exact": [target("lib-1", ["bumper", "step"])]},
        "assets": {
            "lib-1": {
                "bumper": [asset("same-bumper"), asset("same-bumper")],
                "step": [asset("lib-1-step")],
            },
        },
        "verify": {"same-bumper": ok(), "lib-1-step": ok()},
    }
    with tempfile.TemporaryDirectory() as td:
        summary, world = run_engine(b, w, root=td)
        assert summary["state"] == "DONE", summary
        assert world.calls["verify"] == 2, world.calls  # bumper 去重后 1 + step 1


def test_same_asset_covers_multiple_parts():
    """一张整车图可以同时是多个部件的证据（M1 loop 暴露的绑定 bug 回归）。"""
    b = base_brief(parts=("bumper", "step"))
    w = {
        "library": {"u-exact": [target("lib-1", ["bumper", "step"])]},
        "assets": {"lib-1": {"bumper": [asset("shared")], "step": [asset("shared")]}},
        "verify": {"shared": ok()},
    }
    with tempfile.TemporaryDirectory() as td:
        summary, world = run_engine(b, w, root=td)
        assert summary["state"] == "DONE", summary
        assert summary["accepted_targets"]["u-exact"] == ["lib-1"], summary
        assert world.calls["verify"] == 2, world.calls   # 每个部件各核一次


def test_second_tier_does_not_steal_target():
    """同一车型被 environment 层再次发现时，不能抢走 exact 层的证据（M1 回归）。"""
    b = base_brief(parts=("bumper", "step"), tiers=("exact", "environment"))
    w = {
        "library": {},
        "external": {"u-exact": [target("m1", ["bumper", "step"])],
                     "u-environment": [target("m1", ["bumper", "step"])]},
        "assets": {"m1": {"bumper": [asset("a1")], "step": [asset("a1")]}},
        "verify": {"a1": ok()},
    }
    with tempfile.TemporaryDirectory() as td:
        summary, world = run_engine(b, w, root=td)
        assert summary["accepted_targets"]["u-exact"] == ["m1"], summary
        # 全局只算一次，不因两个层级各占一个槽
        assert summary["slots"]["accepted"] == 1, summary


def test_event_log():
    b = base_brief()
    w = {
        "library": {"u-exact": [target("lib-1", ["bumper", "step"])]},
        "assets": {
            "lib-1": {"bumper": [asset("lib-1-bumper")], "step": [asset("lib-1-step")]},
        },
        "verify": {"lib-1-bumper": ok(), "lib-1-step": ok()},
    }
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        events = RunStore(td, "t1").read_events()
        transitions = [(e["from"], e["to"]) for e in events
                       if e.get("action") == "transition"]
        assert ("LIBRARY_SEARCH", "FETCH") in transitions, transitions
        assert ("FETCH", "VERIFY") in transitions, transitions
        assert ("WRITEBACK",) not in transitions
        assert summary["state"] == "DONE"


def test_fixture_demo():
    brief = json.loads((FIX / "brief-desert.json").read_text(encoding="utf-8"))
    world = json.loads((FIX / "world-desert.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(brief, world, run_id="demo", root=td)
        assert summary["state"] == "DONE", summary
        assert summary["coverage"]["u-exact"]["accepted"] == 2, summary
        assert summary["coverage"]["u-env"]["accepted"] == 1, summary
        assert not summary["gaps"], summary


def test_json_schema_contracts():
    brief = json.loads((FIX / "brief-desert.json").read_text(encoding="utf-8"))
    brief_schema = json.loads((ROOT / "schemas" / "task-brief-v3.schema.json")
                              .read_text(encoding="utf-8"))
    jsonschema.validate(brief, brief_schema)

    state_schema = json.loads((ROOT / "schemas" / "retrieval-state.schema.json")
                              .read_text(encoding="utf-8"))
    event_schema = json.loads((ROOT / "schemas" / "retrieval-event.schema.json")
                              .read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(
            brief,
            json.loads((FIX / "world-desert.json").read_text(encoding="utf-8")),
            run_id="schema", root=td)
        assert summary["state"] == "DONE", summary
        state = json.loads(Path(summary["state_path"]).read_text(encoding="utf-8"))
        jsonschema.validate(state, state_schema)
        for line in Path(summary["events_path"]).read_text(encoding="utf-8").splitlines():
            jsonschema.validate(json.loads(line), event_schema)


def test_web_only_world_rule_verify_and_evidence():
    b = base_brief(slots=1)
    parts = Brief.from_dict(b).parts_by_key

    def make_asset(target, part):
        return Asset(
            asset_id=f"{target.model}-{part}", target_id=target.target_id,
            part=part, view="front", width=1600, height=900,
            url="https://example.test/a.jpg", title=f"{target.model} 6x6 工程车",
            model=target.model, channel="360", status="gated")

    world = WebWorld({"u-exact": ["model-1"]}, parts,
                     fetch_fn=lambda t, p: [make_asset(t, p)])
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "evidence.db"
        store = EvidenceStore(db)
        engine = RetrievalEngine(
            Brief.from_dict(b), world, run_root=td, run_id="t-web",
            evidence_writer=lambda rows: store.write_rows("t-web", rows))
        summary = engine.run()
        assert summary["state"] == "DONE", summary
        assert summary["coverage"]["u-exact"]["accepted"] == 1, summary
        assert store.count() == 2, store.count()


def test_rule_verifier_rejects_bad_asset():
    part = PartRequirement(part="bumper", label="保险杠", views=("front",),
                           design_relevance="strong", accept="A")
    verifier = RuleVerifier({"bumper": part})
    bad = Asset(asset_id="bad", target_id="t", part="bumper", view="side",
                width=400, height=300, title="other truck", model="model-1")
    v = verifier.verify(bad, "bumper")
    assert not v.accepted
    assert "low_resolution" in v.defects
    assert "wrong_identity" in v.defects
    # 视角从硬缺陷降为 warning：CLIP 视角 top1−top2 中位数 ~0.003，不可当门槛
    assert "view_mismatch" in v.warnings
    assert "wrong_view" not in v.defects
    good = Asset(asset_id="good", target_id="t", part="bumper", view="front",
                 width=1600, height=900, title="model-1 6x6", model="model-1")
    assert verifier.verify(good, "bumper").accepted
    # 视角不符但其余合格：仍接受，只留 warning
    good_side = Asset(asset_id="good-side", target_id="t", part="bumper",
                      view="side", width=1600, height=900,
                      title="model-1 6x6", model="model-1")
    sv = verifier.verify(good_side, "bumper")
    assert sv.accepted, sv
    assert "view_mismatch" in sv.warnings, sv


def test_null_library_adapter():
    assert NullLibraryAdapter().targets(None) == []


if __name__ == "__main__":
    check("任务单校验", test_brief_validation)
    check("JSON Schema 契约", test_json_schema_contracts)
    check("库内优先，不触发外检", test_library_first_no_external)
    check("库内被拒 → 外检补位", test_external_fallback_after_library_reject)
    check("exact 耗尽 → environment 降级", test_degrade_to_next_tier)
    check("全失败 → FAILED + 缺口报告", test_gap_report_when_all_fail)
    check("续跑跳过已完成", test_resume_skips_finished_run)
    check("重复资产去重", test_idempotent_asset_dedupe)
    check("同图可覆盖多部件", test_same_asset_covers_multiple_parts)
    check("跨层不抢证据", test_second_tier_does_not_steal_target)
    check("事件日志记录转移", test_event_log)
    check("夹具演示案例", test_fixture_demo)
    check("网页-only + 规则核验 + 证据落库", test_web_only_world_rule_verify_and_evidence)
    check("规则核验拒绝坏资产", test_rule_verifier_rejects_bad_asset)
    check("空库适配器", test_null_library_adapter)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"retrieval_engine: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
