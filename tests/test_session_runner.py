# -*- coding: utf-8 -*-
"""L1 SessionRunner 测试：入口/边界 patch/持久化续跑/确认。"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

import test_retrieval_engine as TE  # noqa: E402
from equiplens.retrieval_engine.adapters import FakeWorld  # noqa: E402
from equiplens.session_runner import SessionRunner  # noqa: E402

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        RESULTS.append((name, "FAIL", str(e)[:300]))


def world_for(tid="t1", aid="a1"):
    return {"external": {"u-exact": [TE.target(tid, ["bumper"])]},
            "assets": {tid: {"bumper": [TE.asset(aid)]}},
            "verify": {aid: TE.ok()}}


def test_offline_patch_applied_and_delivered():
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        store = Path(td) / "s.json"
        r = SessionRunner(b, FakeWorld(world_for()), run_root=td, run_id="s1", store_path=store)
        res = r.send("都要侧面", msg_id="m1")
        assert res["ok"] and res["patches"][0]["target"] == "fetch.filters.views", res
        out = r.run()
        assert r.applied >= 1, out
        assert "side" in r.engine.brief.parts_by_key["bumper"].views, r.engine.brief.parts_by_key
        assert out["delivered"] == 1, out
        assert out["session"]["state"] == "DELIVERED", out["session"]
        assert store.exists()


def test_persistence_and_resume():
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        store = Path(td) / "s.json"
        r = SessionRunner(b, FakeWorld(world_for()), run_root=td, run_id="s2", store_path=store)
        r.send("都要侧面", msg_id="m2")
        for _ in range(2):
            r.step()
        r.save()
        payload = json.loads(store.read_text(encoding="utf-8"))
        assert payload["session"]["pending"] or payload["session"]["patches"], payload["session"]

        r2 = SessionRunner.load(store, FakeWorld(world_for()))
        assert r2.session.pending and r2.session.pending[0].target == "fetch.filters.views"
        out = r2.run()
        assert out["delivered"] == 1, out
        assert out["session"]["state"] == "DELIVERED", out["session"]


def test_ambiguous_destructive_requires_confirm():
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        r = SessionRunner(b, FakeWorld(world_for()), run_root=td, run_id="s3",
                          store_path=Path(td) / "s.json")
        res = r.send("删掉一张", msg_id="m3")
        assert res.get("clarify"), res
        out = r.confirm(False)
        assert out["ok"] and not r.session.pending, out
        assert r.session.state.value in ("PLANNING", "RUNNING"), r.session.state


def test_no_message_no_patches():
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        r = SessionRunner(b, FakeWorld(world_for()), run_root=td, run_id="s4",
                          store_path=Path(td) / "s.json")
        out = r.run()
        assert r.applied == 0, r.applied
        assert out["delivered"] == 1, out
        cfg = r.engine._summary(r.state).get("config") or {}
        assert cfg.get("session_patches") == 0, cfg


def test_report_intent_recorded():
    from equiplens.session_router import guard
    out = guard("出报告吧，PPT 版本给我", {"targets": ["delivery.report"], "confidence": 0.9})
    assert out["targets"] == ["delivery.report"] and not out["hard"], out
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        r = SessionRunner(b, FakeWorld(world_for()), run_root=td, run_id="s5",
                          store_path=Path(td) / "s.json")
        r.send("出报告吧，PPT 版本给我", msg_id="m5",
               result={"targets": ["delivery.report"], "confidence": 0.9})
        r.run()
        from equiplens.session import Patch  # noqa: F401
        assert any(p.get("target") == "delivery.report" for p in r.session.patches), r.session.patches
        assert r.summary()["report_requested"] is True
        assert r.summary()["delivery_format"] == "both", r.summary()


def test_quantity_semantics():
    from equiplens.session_router import guard
    # 显式总数/凑够 N：改总数，不是同款补图
    out = guard("同款再加两台吧，凑 12 个。", {"targets": ["plan.quantity"], "hard": True,
                                              "confidence": 0.9})
    assert out["targets"] == ["plan.quantity"] and out["hard"] is True, out
    # 同款 + 无总数：同车补图
    out2 = guard("同款再来三张", {"targets": ["plan.quantity"], "hard": True, "confidence": 0.9})
    assert out2["targets"] == ["fill.quota"] and out2["hard"] is False, out2
    # 每款张数：条件扩张
    out3 = guard("每个车型统一按6张来", {"targets": ["plan.quantity"], "hard": True,
                                         "confidence": 0.9})
    assert out3["targets"] == ["plan.quantity_per_model"] and out3["hard"] is False, out3
    assert out3["values"]["plan.quantity_per_model"]["count"] == 6, out3
    # 能力门
    out4 = guard("别给我带水印的图", {"targets": ["fetch.filters.quality"], "confidence": 0.9})
    assert out4["targets"] == [] and out4["feasibility"] == "unsupported", out4
    assert out4["action"] == "explain" and out4["message"], out4
    # 部分能力：换图可做、原图保证不可做
    out5 = guard("第4张换成高清原图", {"targets": ["delivered.replace", "fetch.filters.quality"],
                                       "confidence": 0.9})
    assert out5["targets"] == ["delivered.replace"], out5
    assert out5["feasibility"] == "partial" and out5["message"], out5
    # 阶段门：交付前不许资产级动作
    out6 = guard("第3张换掉", {"targets": ["delivered.replace"], "confidence": 0.9},
                 context={"stage": "pre_run"})
    assert out6["targets"] == [] and out6["action"] == "clarify", out6
    # 交付后允许
    out7 = guard("第3张换掉", {"targets": ["delivered.replace"], "confidence": 0.9},
                 context={"stage": "delivered"})
    assert out7["targets"] == ["delivered.replace"], out7


def test_two_messages_before_run_keep_both_patches():
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        r = SessionRunner(b, FakeWorld(world_for()), run_root=td, run_id="s6",
                          store_path=Path(td) / "s.json")
        r.run_until("FETCH", require_targets=True)
        r.send("都要侧面", msg_id="a")
        r.send("要高清", msg_id="b")
        targets = [p["target"] for p in r.session.patches] + [p.target for p in r.session.pending]
        assert "fetch.filters.views" in targets, targets
        assert "fetch.filters.quality" in targets, targets


def test_extract_values_fill_quota_and_views():
    from equiplens.session import extract_values
    v = extract_values("同款再加两台吧", ["fill.quota"])
    assert v["fill.quota"]["count"] == 2, v
    v2 = extract_values("都要侧面", ["fetch.filters.views"])
    assert v2["fetch.filters.views"]["views"] == ["side"], v2


def test_create_from_text_builds_brief_without_patch():
    import equiplens.briefing as B
    from unittest import mock

    def fake_generate(text, key, **kw):
        assert kw.get("use_taskspec") is True, kw
        return {"brief": TE.base_brief(parts=("bumper",), slots=1), "taskspec": {}}

    with tempfile.TemporaryDirectory() as td:
        with mock.patch.object(B, "generate_brief", fake_generate):
            r = SessionRunner.create_from_text(
                "沙漠牵引车 10 台", "sk-test", run_root=td, run_id="s7",
                store_path=Path(td) / "s.json",
                build_world=lambda brief: FakeWorld(world_for()))
        assert r.session.patches == [] and not r.session.pending, r.session.patches
        assert r.created_from_text == "沙漠牵引车 10 台"
        out = r.run()
        assert out["delivered"] == 1, out


def test_unsupported_explain_no_patch():
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        r = SessionRunner(b, FakeWorld(world_for()), run_root=td, run_id="s8",
                          store_path=Path(td) / "s.json")
        res = r.send("别给我带水印的图", msg_id="u1",
                     result={"targets": [], "action": "explain", "feasibility": "unsupported",
                             "message": "去水印暂不支持"})
        assert res.get("explain") is True, res
        assert not r.session.pending and not r.session.patches, (r.session.pending, r.session.patches)


def test_post_delivery_remove_records_replenish():
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        r = SessionRunner(b, FakeWorld(world_for()), run_root=td, run_id="s9",
                          store_path=Path(td) / "s.json")
        r.run()
        res = r.send("第1张删掉", msg_id="d1",
                     result={"targets": ["delivered.remove"], "asset_index": 1,
                             "destructive": True, "confirm": False, "hard": False,
                             "confidence": 0.9})
        assert res["ok"], res
        assert r.summary()["pending_replenish"] == 1, r.summary()
        assert any(d.get("status") == "superseded" for d in r.session.delivered), r.session.delivered


def test_per_model_patch_reaches_engine():
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        r = SessionRunner(b, FakeWorld(world_for()), run_root=td, run_id="s10",
                          store_path=Path(td) / "s.json")
        r.run_until("FETCH", require_targets=True)
        r.send("每款6张", msg_id="pm1",
               result={"targets": ["plan.quantity_per_model"], "confidence": 0.9,
                       "values": {"plan.quantity_per_model": {"count": 6}}})
        r.run()
        assert r.state.get("per_model_quota") == 6, r.state.get("per_model_quota")


if __name__ == "__main__":
    for name, fn in [(k, v) for k, v in sorted(globals().items())
                     if k.startswith("test_") and callable(v)]:
        check(name, fn)
    fails = [r for r in RESULTS if r[1] == "FAIL"]
    for name, status, err in RESULTS:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"session_runner: {len(RESULTS) - len(fails)}/{len(RESULTS)} 通过")
    sys.exit(1 if fails else 0)
