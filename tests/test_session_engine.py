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


if __name__ == "__main__":
    for name, fn in [(k, v) for k, v in sorted(globals().items())
                     if k.startswith("test_") and callable(v)]:
        check(name, fn)
    fails = [r for r in RESULTS if r[1] == "FAIL"]
    for name, status, err in RESULTS:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"session_engine: {len(RESULTS) - len(fails)}/{len(RESULTS)} 通过")
    sys.exit(1 if fails else 0)
