# -*- coding: utf-8 -*-
"""S0-05 × 检索引擎（FakeWorld）集成测试：M4。"""
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
from equiplens.retrieval_engine import Brief, RetrievalEngine  # noqa: E402
from equiplens.retrieval_engine.adapters import FakeWorld  # noqa: E402
from equiplens.session import Session, SessionState  # noqa: E402

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        RESULTS.append((name, "FAIL", str(e)[:200]))


def world_for(tid="ext-1", aid="a1"):
    return {"external": {"u-exact": [TE.target(tid, ["bumper"])]},
            "assets": {tid: {"bumper": [TE.asset(aid)]}},
            "verify": {aid: TE.ok()}}


def test_engine_step_then_resume():
    b = TE.base_brief(parts=("bumper",), slots=1)
    w = world_for()
    with tempfile.TemporaryDirectory() as td:
        e = RetrievalEngine(Brief.from_dict(b), FakeWorld(w), run_root=td, run_id="r1")
        st = e._load_or_init()
        for _ in range(2):
            st = e.step(st)
        assert not st.get("finished"), st["state"]
        # 模拟崩溃后新进程：同一 run_root/run_id 续跑
        e2 = RetrievalEngine(Brief.from_dict(b), FakeWorld(w), run_root=td, run_id="r1")
        summary = e2.run()
        assert summary["delivery"]["delivered"] == 1, summary["delivery"]


def test_session_checkpoint_between_engine_steps():
    b = TE.base_brief(parts=("bumper",), slots=1)
    w = world_for()
    with tempfile.TemporaryDirectory() as td:
        e = RetrievalEngine(Brief.from_dict(b), FakeWorld(w), run_root=td, run_id="r2")
        st = e._load_or_init()
        st = e.step(st)
        s = Session(b)
        s.start()
        s.checkpoint(st["state"])
        r = s.interrupt("都要正脸", msg_id="e1")
        assert r["ok"] and not r["hard"], r
        s.checkpoint(st["state"])
        assert s.version == 2 and s.patches[0]["target"] == "fetch.filters.views"
        # 引擎继续跑完，session 不阻塞
        for _ in range(20):
            if st.get("finished"):
                break
            st = e.step(st)
        assert st.get("finished"), st["state"]


def test_session_delivery_edit_no_confirm():
    s = Session({"request": {"class": "沙漠牵引车"}})
    s.deliver([{"url": "u1", "sha1": "s1", "model": "X3000", "target": "u-exact"},
               {"url": "u2", "sha1": "s2", "model": "X3000", "target": "u-exact"}])
    r = s.interrupt("删掉第 1 张", msg_id="e2")
    assert not r.get("clarify") and r["hard"] is False, r
    s.checkpoint("FILL")
    assert len(s.delivered) == 2  # 不物理删除
    assert any(d["status"] == "superseded" for d in s.delivered)


def test_correction_marks_only_one_asset():
    s = Session({"request": {"class": "沙漠牵引车"}})
    s.deliver([{"asset_id": "a1", "url": "u1", "sha1": "s1", "model": "X3000", "target": "u-exact"},
               {"asset_id": "a2", "url": "u2", "sha1": "s2", "model": "X3000", "target": "u-exact"},
               {"asset_id": "a3", "url": "u3", "sha1": "s3", "model": "X3000", "target": "u-exact"}])
    r = s.interrupt("第 2 张不对，不是沙漠版", msg_id="e3")
    assert r["ok"] and not r.get("clarify"), r
    s.checkpoint("VERIFY")
    superseded = [d for d in s.delivered if d["status"] == "superseded"]
    assert len(superseded) == 1 and superseded[0]["asset_id"] == "a2", s.delivered
    assert s.blacklist and s.blacklist[0]["asset"] == "a2", s.blacklist


def test_delete_marks_only_one_asset():
    s = Session({"request": {"class": "沙漠牵引车"}})
    s.deliver([{"asset_id": "b1", "url": "u1", "sha1": "s1", "model": "X3000", "target": "u-exact"},
               {"asset_id": "b2", "url": "u2", "sha1": "s2", "model": "X3000", "target": "u-exact"}])
    s.interrupt("删掉第 2 张", msg_id="e4")
    s.checkpoint("FILL")
    assert [d["status"] for d in s.delivered] == ["active", "superseded"], s.delivered


def test_original_index_after_supersede():
    s = Session({"request": {"class": "沙漠牵引车"}})
    s.deliver([{"asset_id": "c1", "url": "u1", "sha1": "s1", "model": "X3000", "target": "u-exact"},
               {"asset_id": "c2", "url": "u2", "sha1": "s2", "model": "X3000", "target": "u-exact"},
               {"asset_id": "c3", "url": "u3", "sha1": "s3", "model": "X3000", "target": "u-exact"}])
    r = s.interrupt("第 1 张不对", msg_id="o1")
    assert r["patches"][0]["value"]["index_basis"] == "original", r
    s.checkpoint("VERIFY")
    s.interrupt("删掉第 2 张", msg_id="o2"); s.checkpoint("FILL")
    status = {d["seq"]: d["status"] for d in s.delivered}
    assert status == {1: "superseded", 2: "superseded", 3: "active"}, status


def test_added_brand_delta_run():
    """新增品牌走 delta run：旧 target 不重抓，交付只增不减。"""
    b1 = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        w1 = FakeWorld(world_for("x3000", "a-x"))
        s1 = RetrievalEngine(Brief.from_dict(b1), w1, run_root=td, run_id="base")
        s1.run()
        s = Session(b1)
        s.deliver([{"url": "u-x", "sha1": "s-x", "model": "X3000", "target": "u-exact"}])
        # 第二段 delta：只给新品牌的数据
        w2 = FakeWorld(world_for("howo", "a-h"))
        s2 = RetrievalEngine(Brief.from_dict(b1), w2, run_root=td, run_id="delta")
        s2.run()
        assert w2.calls["fetch"] == 1, w2.calls
        s.deliver([{"url": "u-h", "sha1": "s-h", "model": "HOWO", "target": "u-exact"}])
        assert len(s.delivered) == 2
        assert all(d["status"] == "active" for d in s.delivered)


def _advance(e, st, pred, limit=14):
    for _ in range(limit):
        if pred(st) or st.get("finished"):
            return st
        st = e.step(st)
    return st


def _at_fetch_with_targets(e, st):
    return _advance(e, st, lambda s: s.get("state") == "FETCH" and s.get("active_targets"))


def test_views_patch_reaches_part_requirement():
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        e = RetrievalEngine(Brief.from_dict(b), FakeWorld(world_for()), run_root=td, run_id="v1")
        st = _at_fetch_with_targets(e, e._load_or_init())
        s = Session(b)
        s.start()
        r = s.interrupt("都要侧面", msg_id="v1")
        assert r["ok"] and not r.get("clarify"), r
        s.apply_pending()
        assert s.patches[0]["target"] == "fetch.filters.views", s.patches
        assert s.patches[0]["value"]["data"] == {"views": ["side"]}, s.patches[0]["value"]
        res = e.apply_patches(st, s.patches)
        assert res["applied"] == ["fetch.filters.views"], res
        assert "side" in e.brief.parts_by_key["bumper"].views
        out = s.apply_to_brief(b)
        assert "side" in out["part_requirements"][0]["views"]


def test_quality_patch_sets_min_width():
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        e = RetrievalEngine(Brief.from_dict(b), FakeWorld(world_for()), run_root=td, run_id="q1")
        st = e._load_or_init()
        res = e.apply_patches(st, [{"target": "fetch.filters.quality",
                                    "value": {"data": {"min_width": 1600}}}])
        assert res["applied"] == ["fetch.filters.quality"], res
        assert e.brief.request["min_width"] == 1600


def test_negative_patch_filters_fill():
    def world(model):
        return {"external": {"u-exact": [TE.target("t-howo", ["bumper"])]},
                "assets": {"t-howo": {"bumper": [dict(TE.asset("a1"), model=model)]}},
                "verify": {"a1": TE.ok()}}
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        e = RetrievalEngine(Brief.from_dict(b), FakeWorld(world("HOWO TX")), run_root=td, run_id="n1")
        st = _at_fetch_with_targets(e, e._load_or_init())
        s = Session(b)
        s.start()
        r = s.interrupt("不要 HOWO", msg_id="n1",
                        result={"targets": ["plan.negative"],
                                "values": {"plan.negative": {"terms": ["HOWO"]}},
                                "confidence": 0.9})
        assert r["ok"], r
        s.apply_pending()
        e.apply_patches(st, s.patches)
        summary = e.run()
        assert summary["delivery"]["delivered"] == 0, summary["delivery"]
        e2 = RetrievalEngine(Brief.from_dict(b), FakeWorld(world("HOWO TX")), run_root=td, run_id="n2")
        assert e2.run()["delivery"]["delivered"] == 1


def test_add_targets_patch_only_fetches_new():
    w = {"external": {"u-exact": [TE.target("old", ["bumper"])]},
         "assets": {"old": {"bumper": [TE.asset("a-old")]},
                    "howo-8x4": {"bumper": [TE.asset("a-new")]}},
         "verify": {"a-old": TE.ok(), "a-new": TE.ok()}}
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        e = RetrievalEngine(Brief.from_dict(b), FakeWorld(w), run_root=td, run_id="d1")
        st = _at_fetch_with_targets(e, e._load_or_init())
        s = Session(b)
        s.start()
        r = s.interrupt("把 HOWO 8x4 加进来", msg_id="d1",
                        result={"targets": ["plan.add_targets"],
                                "values": {"plan.add_targets": {"models": ["HOWO 8x4"]}},
                                "confidence": 0.9})
        assert r["ok"], r
        s.apply_pending()
        res = e.apply_patches(st, s.patches)
        assert res["added_targets"] == ["HOWO 8x4"], res
        assert st["active_targets"] == ["howo-8x4"], st["active_targets"]
        summary = e.run()
        assert summary["delivery"]["delivered"] == 1, summary["delivery"]
        assert e.world.calls["fetch"] == 1, e.world.calls


def test_parts_patch_adds_requirement():
    b = TE.base_brief(parts=("bumper",), slots=1)
    with tempfile.TemporaryDirectory() as td:
        e = RetrievalEngine(Brief.from_dict(b), FakeWorld(world_for()), run_root=td, run_id="p1")
        st = e._load_or_init()
        res = e.apply_patches(st, [{"target": "fetch.parts",
                                    "value": {"data": {"parts": ["grille"]}}}])
        assert res["applied"] == ["fetch.parts:grille"], res
        assert "grille" in e.brief.parts_by_key


if __name__ == "__main__":
    for name, fn in [(k, v) for k, v in sorted(globals().items())
                     if k.startswith("test_") and callable(v)]:
        check(name, fn)
    fails = [r for r in RESULTS if r[1] == "FAIL"]
    for name, status, err in RESULTS:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"session_engine: {len(RESULTS) - len(fails)}/{len(RESULTS)} 通过")
    sys.exit(1 if fails else 0)
