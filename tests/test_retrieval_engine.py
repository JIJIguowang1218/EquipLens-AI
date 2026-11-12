# -*- coding: utf-8 -*-
"""检索中引擎 P1 测试：契约/库内优先/外检/降级/缺口/续跑/事件（全离线）。"""

import copy
import json
import sys
import tempfile
import types
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens.retrieval_engine import (Asset, Brief, PartRequirement,  # noqa: E402
                                       RetrievalEngine, RunStore, Target,
                                       validate_brief)
from equiplens.retrieval_engine.adapters import FakeWorld  # noqa: E402
from equiplens.retrieval_engine.evidence import EvidenceStore  # noqa: E402
from equiplens.retrieval_engine import cli as engine_cli  # noqa: E402
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
               slots=1, backup=0):
    # backup 默认 0：多数单测只测主槽，不触发备选补抓；备选用例显式传 backup=4
    return {
        "brief_id": "b-test",
        "request": {"class": "沙漠牵引车",
                    "page_budget": {"vehicle_slots": slots,
                                    "backup_slots": backup}},
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


def asset(aid, view="front", scene="", overview=False):
    return {"asset_id": aid, "view": view, "width": 1600, "height": 900,
            "scene": scene, "overview": overview}


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


def test_asset_contract_keeps_scene():
    a = Asset(asset_id="a", target_id="t", part="bumper", scene="single_vehicle",
              overview=True)
    d = a.to_dict()
    assert d["scene"] == "single_vehicle" and d["overview"] is True, d
    b = Asset.from_dict(d, target_id="t", part="bumper")
    assert b.scene == "single_vehicle" and b.overview is True


def test_fill_marks_part_only_without_single_vehicle():
    b = base_brief(slots=1)
    w = {
        "library": {},
        "external": {"u-exact": [target("ext-1", ["bumper"])]},
        "assets": {"ext-1": {"bumper": [asset("ext-1-bumper", scene="part")]}},
        "verify": {"ext-1-bumper": ok()},
    }
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        st = json.loads((Path(td) / "t1" / "state.json").read_text(encoding="utf-8"))
        assert st["targets"]["ext-1"]["part_only"] is True, st["targets"]["ext-1"]
        assert summary["coverage"]["u-exact"]["accepted"] == 1


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
        assert summary["coverage"]["u-exact"]["accepted"] >= 1, summary
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
        # 验收=每台车至少 1 张通过核验的图（部件可见性不在当前验收内）：
        # 因此库内两条都判坏，才会触发外检补位。
        "verify": {
            "lib-1-bumper": bad(), "lib-1-step": bad(),
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
        assert not summary["gaps"], summary
        # 验收口径=每台车 ≥1 张通过核验的图，所以每个单元会把 3 个候选都收下
        assert summary["coverage"]["u-exact"]["accepted"] >= 2, summary
        assert summary["slots"]["filled"], summary


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
        assert summary["coverage"]["u-exact"]["accepted"] >= 1, summary
        assert store.count() == 2, store.count()


def test_rule_verifier_rejects_bad_asset():
    part = PartRequirement(part="bumper", label="保险杠", views=("front",),
                           design_relevance="strong", accept="A")
    verifier = RuleVerifier({"bumper": part})
    bad = Asset(asset_id="bad", target_id="t", part="bumper", view="side",
                width=400, height=300, title="other truck", model="model-1")
    v = verifier.verify(bad, "bumper")
    assert not v.accepted
    # 分辨率降为 warning（只记档位，不否决）
    assert "low_resolution" in v.warnings
    assert "low_resolution" not in v.defects
    # 身份改为分级：对不上型号 → unknown（不再直接判 wrong_identity）
    assert v.identity == "unknown", v
    assert "identity_unverified" in v.warnings, v
    # 构型矛盾仍是硬缺陷
    wrong_cfg = Asset(asset_id="cfg", target_id="t", part="bumper", view="front",
                      width=1600, height=900, title="model-1 8x4",
                      model="model-1 6x6")
    cv = verifier.verify(wrong_cfg, "bumper")
    assert not cv.accepted and "wrong_config" in cv.defects, cv
    # 视角从硬缺陷降为 warning：CLIP 视角 top1−top2 中位数 ~0.003，不可当门槛
    assert "view_mismatch" in v.warnings
    assert "wrong_view" not in v.defects
    good = Asset(asset_id="good", target_id="t", part="bumper", view="front",
                 width=1600, height=900, title="model-1 6x6", model="model-1")
    assert verifier.verify(good, "bumper").accepted
    # 视角不符但其余合格：仍接受，只留 warning
    low = Asset(asset_id="low", target_id="t", part="bumper", view="front",
                width=640, height=480, title="model-1 6x6", model="model-1")
    lv = verifier.verify(low, "bumper")
    assert lv.accepted and "low_resolution" in lv.warnings, lv
    good_side = Asset(asset_id="good-side", target_id="t", part="bumper",
                      view="side", width=1600, height=900,
                      title="model-1 6x6", model="model-1")
    sv = verifier.verify(good_side, "bumper")
    assert sv.accepted, sv
    assert "view_mismatch" in sv.warnings, sv


def test_unit_quota_caps_accepted_targets():
    """单元配额是硬上限：quota=1 的单元不能因为一批 2 台都合格就占 2 槽。"""
    b = base_brief(parts=("bumper",), slots=3)
    b["research_units"][0]["quota"] = 1
    w = {
        "library": {"u-exact": [target("a", ["bumper"]), target("b", ["bumper"])]},
        "assets": {"a": {"bumper": [asset("a1")]},
                   "b": {"bumper": [asset("b1")]}},
        "verify": {"a1": ok(), "b1": ok()},
    }
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        assert len(summary["accepted_targets"]["u-exact"]) == 1, summary
        assert summary["delivery"]["status"] == "short", summary["delivery"]


def test_web_world_requires_plan_or_models():
    """discover fallback 已废弃：无 plan/无 models 必须显式报错，不能静默国产-only。"""
    part = PartRequirement(part="bumper", label="保险杠", views=("front",),
                           design_relevance="strong", accept="A")
    world = WebWorld({}, {"bumper": part}, citation_check=False)
    unit = types.SimpleNamespace(unit_id="u-exact", tier="exact",
                                 parts=("bumper",), scope="沙漠牵引车")
    try:
        world.external_targets(unit)
    except RuntimeError as e:
        assert "discover fallback" in str(e), e
    else:
        raise AssertionError("应当抛 RuntimeError")


def test_cli_web_only_without_plan_errors():
    """CLI 在联网前就拦住无 plan/无 models 的 --web-only。"""
    brief = str(FIX / "brief-desert.json")
    try:
        engine_cli.main(["--brief", brief, "--web-only", "--run-id", "should-not-run"])
    except SystemExit as e:
        assert e.code == 2, e.code
    else:
        raise AssertionError("应当 parser.error 退出 2")


def test_target_identity_kind_roundtrip():
    """identity_kind 只随 target 传播/展示，不参与淘汰。"""
    t = Target(target_id="x", model="X", source="plan", tier="exact",
               parts=("step",), identity_kind="generic")
    d = t.to_dict()
    assert d["identity_kind"] == "generic", d
    assert Target.from_dict(d, source="plan", tier="exact").identity_kind == "generic"


def test_plan_partition_reserves_unit_quotas():
    """unit 配额预留 primary：exact 的补位不能抢 environment 的前 4 个 primary。"""
    part = PartRequirement(part="bumper", label="保险杠", views=("front",))
    plan = [{"model": f"m{i}", "identity_kind": "code", "intent_rank": i + 1,
             "role": "primary" if i < 4 else "backup", "citation_ok": True}
            for i in range(8)]
    world = WebWorld({}, {"bumper": part}, plan=plan, citation_check=False,
                     unit_quotas={"u-exact": 2, "u-env": 2})
    u1 = types.SimpleNamespace(unit_id="u-exact", tier="exact",
                               parts=("bumper",), quota=2, scope="x")
    u2 = types.SimpleNamespace(unit_id="u-env", tier="environment",
                               parts=("bumper",), quota=2, scope="x")
    assert [t.model for t in world.external_targets(u1)] == ["m0", "m1"]
    assert [t.model for t in world.external_targets(u2)] == ["m2", "m3"]
    assert [t.model for t in world.external_targets(u1)] == ["m4", "m5"]


def test_code_prefilter_keeps_match_drops_mismatch():
    assert WebWorld._code_ok("TAZ4922 6×6", "重汽 TAZ4922 牵引车")
    assert not WebWorld._code_ok("TAZ4922 6×6", "重汽 TAZ4413 牵引车")
    assert WebWorld._code_ok("TAZ4922 6×6", "重汽 6×6 牵引车")  # 标题无 code，不拒
    assert WebWorld._code_ok("6×6 沙漠车", "TAZ4413")  # generic target，不拒


def test_null_library_adapter():
    assert NullLibraryAdapter().targets(None) == []


def test_delivery_block_marks_short():
    """交付守卫：要求 1 个车型却一个都没收，必须显式 status=short + missing。"""
    b = base_brief()
    w = {"library": {}, "external": {}, "assets": {}, "verify": {}}
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        d = summary["delivery"]
        assert d["required"] == 1 and d["delivered"] == 0, d
        assert d["missing"] == 1 and d["status"] == "short", d


def test_delivery_counts_degraded_identity():
    """靠 probable 身份占槽的车要计入 degraded，交付不能假装全是 confirmed。"""
    b = base_brief(parts=("bumper",), slots=1)
    w = {
        "library": {"u-exact": [target("lib-1", ["bumper"])]},
        "assets": {"lib-1": {"bumper": [asset("a1")]}},
        "verify": {"a1": {**ok(), "identity": "probable"}},
    }
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        d = summary["delivery"]
        assert d["status"] == "complete", d
        assert d["degraded"] == 1 and d["degraded_targets"] == ["lib-1"], d


def test_part_only_contract_roundtrip():
    """part_only 必须进契约：dataclass ↔ dict ↔ schema，不能只是裸 key。"""
    t = Target(target_id="x", model="X", source="plan", tier="exact",
               parts=("step",), part_only=True)
    d = t.to_dict()
    assert d["part_only"] is True, d
    assert Target.from_dict(d, source="plan", tier="exact").part_only is True
    state = {
        "run_id": "r", "brief_id": "b", "state": "DONE", "finished": True,
        "units": {}, "coverage": {}, "decisions": [],
        "budget_used": {"queries": 0, "models": 0, "fetches": 0, "verifies": 0},
        "targets": {"x": d},
        "attempts": {"x": {"fetched": True, "assets": 2, "verified": 3,
                           "accepted": 2, "filled": True}},
    }
    schema = json.loads((ROOT / "schemas" / "retrieval-state.schema.json")
                        .read_text(encoding="utf-8"))
    jsonschema.validate(state, schema)


def test_attempts_asset_count_is_real():
    """attempts.assets 必须真实计数（旧实现恒为 0，导致不可解释）。"""
    b = base_brief(parts=("bumper",), slots=1)
    w = {
        "external": {"u-exact": [target("ext-1", ["bumper"])]},
        "assets": {"ext-1": {"bumper": [asset("a1"), asset("a2")]}},
        "verify": {"a1": ok(), "a2": ok()},
    }
    with tempfile.TemporaryDirectory() as td:
        run_engine(b, w, root=td)
        st = json.loads((Path(td) / "t1" / "state.json").read_text(encoding="utf-8"))
        att = st["attempts"]["ext-1"]
        assert att["assets"] == 2, att
        assert att["fetches"] if "fetches" in att else True
        assert st["budget_used"]["fetches"] == 2, st["budget_used"]


def test_budget_queries_are_issued_queries_not_targets():
    """budget_used.queries 必须来自 world 的真实计数，不能用候选车型数冒充。"""
    b = base_brief(parts=("bumper",), slots=1)
    w = {"external": {"u-exact": [target("ext-1", ["bumper"])]},
         "assets": {"ext-1": {"bumper": [asset("a1")]}},
         "verify": {"a1": ok()}}
    with tempfile.TemporaryDirectory() as td:
        brief = Brief.from_dict(b)
        world = FakeWorld(w)
        world.query_count = 7          # 模拟：真实发了 7 次搜索请求
        engine = RetrievalEngine(brief, world, run_root=td, run_id="t1")
        summary = engine.run()
        used = summary["budget_used"]
        assert used["queries"] == 7, used           # 不是 1（候选数）
        assert used["models"] == 1, used            # 候选车型数单独记


def test_delivery_required_follows_user_slots():
    """交付台数来自用户输入（brief.page_budget.vehicle_slots），不是写死 12。"""
    b = base_brief(parts=("bumper",), slots=5)
    w = {"external": {"u-exact": [target("ext-1", ["bumper"])]},
         "assets": {"ext-1": {"bumper": [asset("a1")]}},
         "verify": {"a1": ok()}}
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        d = summary["delivery"]
        assert d["required"] == 5, d
        assert d["delivered"] == 1 and d["status"] == "short", d


def test_delivery_backup_four_by_priority():
    """备选固定 4 台：从候选池按 intent_rank 取，不额外检索。"""
    b = base_brief(parts=("bumper",), slots=1, backup=4)
    ext = [{"target_id": f"t{i}", "model": f"m{i}", "parts": ["bumper"],
            "intent_rank": i, "role": "primary" if i == 1 else "backup"}
           for i in range(1, 7)]
    w = {"external": {"u-exact": ext},
         "assets": {f"t{i}": {"bumper": [asset(f"a{i}")]} for i in range(1, 7)},
         "verify": {f"a{i}": ok() for i in range(1, 7)}}
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        d = summary["delivery"]
        assert d["required"] == 1 and d["delivered"] == 1, d
        bk = d["backup"]
        assert bk["required"] == 4, bk
        assert bk["delivered"] == 4, bk
        assert bk["models"] == ["t2", "t3", "t4", "t5"], bk
        assert bk["images"] == 4, bk
        assert bk["short"] == 0, bk


def test_delivery_backup_short_is_visible():
    """候选池不够 4 台时，要显式报 backup.short，不能假装满额。"""
    b = base_brief(parts=("bumper",), slots=1, backup=4)
    ext = [{"target_id": f"t{i}", "model": f"m{i}", "parts": ["bumper"],
            "intent_rank": i} for i in (1, 2)]
    w = {"external": {"u-exact": ext},
         "assets": {f"t{i}": {"bumper": [asset(f"a{i}")]} for i in (1, 2)},
         "verify": {f"a{i}": ok() for i in (1, 2)}}
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        bk = summary["delivery"]["backup"]
        assert bk["delivered"] == 1 and bk["short"] == 3 and bk["models"] == ["t2"], bk


def test_backup_excludes_models_without_images():
    """备选必须有图：没抓到图的车型不进备选，即使意向名次更高。"""
    b = base_brief(parts=("bumper",), slots=1, backup=4)
    ext = [{"target_id": f"t{i}", "model": f"m{i}", "parts": ["bumper"],
            "intent_rank": i} for i in range(1, 8)]
    w = {"external": {"u-exact": ext},
         "assets": {f"t{i}": {"bumper": [asset(f"a{i}")]} for i in range(1, 7)},
         "verify": {f"a{i}": ok() for i in range(1, 7)}}
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        bk = summary["delivery"]["backup"]
        assert "t7" not in bk["models"], bk        # t7 没有任何图
        assert bk["delivered"] == 4 and bk["images"] == 4, bk


def test_backup_short_does_not_fail_the_run():
    """备选补抓不到图时，最多补 3 轮后 DONE + short，不能把成功的 12/12 变成 FAILED。"""
    b = base_brief(parts=("bumper",), slots=1, backup=4)
    w = {"external": {"u-exact": [target("t1", ["bumper"])]},
         "assets": {"t1": {"bumper": [asset("a1")]}},
         "verify": {"a1": ok()}}
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        assert summary["state"] == "DONE", summary["state"]
        bk = summary["delivery"]["backup"]
        assert bk["delivered"] == 0 and bk["short"] == 4, bk
        refills = [d for d in summary["decisions"] if d.get("action") == "backup_refill"]
        assert len(refills) == 3, refills


def test_live_fetch_early_stop_when_all_downloads_fail():
    """一台车连续下载硬失败时早停，不把整批候选全部试完。"""
    from equiplens import imagesearch
    from equiplens.retrieval_engine.web import EARLY_STOP_FAILS
    part = PartRequirement(part="bumper", label="保险杠", views=("front",))
    world = WebWorld({}, {"bumper": part}, citation_check=False)
    t = Target(target_id="t1", model="m1", source="plan", tier="exact",
               parts=("bumper",), unit_id="u-exact")
    hits = [{"url": f"https://dead{i}.example/a.jpg", "title": "m1",
             "channel": "360"} for i in range(20)]
    old_search, old_dl = imagesearch.search_images_hd, imagesearch._download_and_gate
    imagesearch.search_images_hd = lambda *a, **k: (hits, [{"q": "m1"}])
    imagesearch._download_and_gate = lambda hit, health=None: {
        "hit": hit, "data": None, "gate": None, "error": "http 403", "tries": 1}
    try:
        assets = world.live_fetch(t, "bumper")
    finally:
        imagesearch.search_images_hd = old_search
        imagesearch._download_and_gate = old_dl
    st = world.fetch_stats["t1"]
    assert assets == [], assets
    assert st["early_stop"] is True, st
    assert st["failed"] == EARLY_STOP_FAILS, st
    assert world.download_stats()["early_stop_models"] == 1


def test_delivery_explains_unavailable_reasons():
    """未交付候选要能说清为什么：有图但没入选 / 无命中 / 下载全失败。"""
    b = base_brief(parts=("bumper",), slots=1)
    ext = [{"target_id": "t1", "model": "m1", "parts": ["bumper"], "intent_rank": 1},
           {"target_id": "t2", "model": "m2", "parts": ["bumper"], "intent_rank": 2}]
    w = {"external": {"u-exact": ext},
         "assets": {"t1": {"bumper": [asset("a1")]},
                    "t2": {"bumper": [asset("a2")]}},
         "verify": {"a1": ok(), "a2": ok()}}
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        un = {r["model"]: r["reason"] for r in summary["delivery"]["unavailable"]}
        assert un.get("t2") == "not_delivered", un


def test_blocked_hosts_trigger_early_stop():
    """整批结果都来自被拉黑的图床时，也要早停（跳过不再无限继续）。"""
    from equiplens import imagesearch
    part = PartRequirement(part="bumper", label="保险杠", views=("front",))
    world = WebWorld({}, {"bumper": part}, citation_check=False)
    t = Target(target_id="t1", model="m1", source="plan", tier="exact",
               parts=("bumper",), unit_id="u-exact")
    hits = [{"url": f"https://dead.example/{i}.jpg", "title": "m1"} for i in range(20)]
    old_search, old_fetch = imagesearch.search_images_hd, imagesearch._fetch_image
    imagesearch.search_images_hd = lambda *a, **k: (hits, [{"q": "m1"}])

    def _hard_fail(url, referer):
        raise ValueError("http 403")

    imagesearch._fetch_image = _hard_fail
    try:
        world.live_fetch(t, "bumper")
    finally:
        imagesearch.search_images_hd = old_search
        imagesearch._fetch_image = old_fetch
    st = world.fetch_stats["t1"]
    assert st["early_stop"] is True, st
    assert st["failed"] == 3, st          # 同域名，3 次后拉黑
    assert st["blocked"] == 5, st         # 凑满 8 次连续失败后早停，其余不再尝试


def test_summary_records_step_timings():
    """每次 run 要留下每个状态的耗时（交付报告按节点时长复盘的依据）。"""
    b = base_brief(parts=("bumper",), slots=1)
    w = {"external": {"u-exact": [target("t1", ["bumper"])]},
         "assets": {"t1": {"bumper": [asset("a1")]}},
         "verify": {"a1": ok()}}
    with tempfile.TemporaryDirectory() as td:
        summary, _ = run_engine(b, w, root=td)
        timings = summary.get("timings") or []
        assert timings, summary
        assert all("ms" in t and "state" in t for t in timings), timings
        assert summary.get("elapsed_ms") is not None


if __name__ == "__main__":
    check("任务单校验", test_brief_validation)
    check("Asset 保留 scene", test_asset_contract_keeps_scene)
    check("part_only 标记", test_fill_marks_part_only_without_single_vehicle)
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
    check("Target 身份标记往返", test_target_identity_kind_roundtrip)
    check("unit 配额预留 primary", test_plan_partition_reserves_unit_quotas)
    check("code prefilter", test_code_prefilter_keeps_match_drops_mismatch)
    check("无 plan/models 拒绝 fallback", test_web_world_requires_plan_or_models)
    check("CLI 拦截无 plan 的 web-only", test_cli_web_only_without_plan_errors)
    check("交付守卫：不足报 short", test_delivery_block_marks_short)
    check("交付守卫：degraded 身份", test_delivery_counts_degraded_identity)
    check("单元配额是硬上限", test_unit_quota_caps_accepted_targets)
    check("part_only 进契约", test_part_only_contract_roundtrip)
    check("attempts 真实计数", test_attempts_asset_count_is_real)
    check("预算按真实查询计数", test_budget_queries_are_issued_queries_not_targets)
    check("交付台数跟随用户输入", test_delivery_required_follows_user_slots)
    check("备选固定 4 台按优先级", test_delivery_backup_four_by_priority)
    check("备选不足要显式报短", test_delivery_backup_short_is_visible)
    check("备选排除无图车型", test_backup_excludes_models_without_images)
    check("备选补抓不把 run 变 FAILED", test_backup_short_does_not_fail_the_run)
    check("下载全失败时目标级早停", test_live_fetch_early_stop_when_all_downloads_fail)
    check("缺图原因可解释", test_delivery_explains_unavailable_reasons)
    check("拉黑图床触发早停", test_blocked_hosts_trigger_early_stop)
    check("节点耗时记录", test_summary_records_step_timings)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"retrieval_engine: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
