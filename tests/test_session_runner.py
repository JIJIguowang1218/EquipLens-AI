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


def test_increment_is_soft_quota_not_hard_quantity():
    from equiplens.session_router import guard
    out = guard("同款再加两台吧，凑 12 个。", {"targets": ["plan.quantity"], "hard": True,
                                              "confidence": 0.9})
    assert out["targets"] == ["fill.quota"], out
    assert out["hard"] is False, out
    out2 = guard("数量改成 12 台", {"targets": ["plan.quantity"], "hard": True, "confidence": 0.9})
    assert out2["targets"] == ["plan.quantity"] and out2["hard"] is True, out2


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


if __name__ == "__main__":
    for name, fn in [(k, v) for k, v in sorted(globals().items())
                     if k.startswith("test_") and callable(v)]:
        check(name, fn)
    fails = [r for r in RESULTS if r[1] == "FAIL"]
    for name, status, err in RESULTS:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"session_runner: {len(RESULTS) - len(fails)}/{len(RESULTS)} 通过")
    sys.exit(1 if fails else 0)
