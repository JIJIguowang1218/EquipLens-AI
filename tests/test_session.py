# -*- coding: utf-8 -*-
"""S0-05 Session 状态机单测（不联网）。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens.session import Session, SessionState, classify_text  # noqa: E402

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        RESULTS.append((name, "FAIL", str(e)[:200]))


def brief():
    return {"request": {"class": "沙漠牵引车", "page_budget": {"vehicle_slots": 10}}}


def asset(i=1):
    return {"url": f"https://x/{i}.jpg", "sha1": f"sha{i}", "model": "X3000", "target": "u-exact"}


def test_create():
    s = Session(brief())
    assert s.state == SessionState.PLANNING and s.version == 1
    assert s.status()["delivered"] == 0


def test_soft_patch_at_checkpoint():
    s = Session(brief())
    s.start()
    r = s.interrupt("都要正脸", msg_id="m1")
    assert r["ok"] and r["hard"] is False and len(s.pending) == 1, r
    s.checkpoint("FETCH")
    assert s.version == 2 and s.state == SessionState.PLANNING
    assert s.patches[0]["target"] == "fetch.filters.views"
    assert s.brief_versions[0]["hash"] != s.brief_versions[1]["hash"]


def test_clear_destructive_no_confirm():
    s = Session(brief())
    s.deliver([asset(1), asset(2)])
    r = s.interrupt("删掉第2张", msg_id="m2")
    assert not r.get("clarify") and r["hard"] is False, r
    s.checkpoint("FILL")
    assert s.version == 2
    assert any(d["status"] == "superseded" for d in s.delivered)
    assert len(s.delivered) == 2  # 不物理删除


def test_ambiguous_destructive_asks():
    s = Session(brief())
    r = s.interrupt("删掉一张", msg_id="m2b")
    assert r.get("clarify") and s.state == SessionState.CLARIFYING, r


def test_reset_asks():
    s = Session(brief())
    r = s.interrupt("全部重来", msg_id="m2c")
    assert r.get("clarify") and s.state == SessionState.CLARIFYING, r


def test_chinese_index_clear_target():
    r = classify_text("第三张换掉")
    assert r["asset_index"] == 3 and r["confirm"] is False, r


def test_negative_is_hard_constraint_soft_interrupt():
    r = classify_text("不要挂车，不要内饰")
    assert r["hard"] is False and r["enforce"] == "hard", r
    assert "plan.negative" in r["targets"]


def test_pause_resume():
    s = Session(brief())
    s.start()
    r = s.interrupt("先停一下", msg_id="m4")
    assert r["hard"] and s.state == SessionState.PAUSED, r
    s.resume()
    assert s.state == SessionState.RUNNING and s.version == 2


def test_idempotent_message():
    s = Session(brief())
    s.interrupt("要正脸", msg_id="same")
    n = len(s.pending)
    r = s.interrupt("要正脸", msg_id="same")
    assert r.get("duplicate") and len(s.pending) == n


def test_invalid_target_rejected():
    s = Session(brief())
    r = s.interrupt("x", msg_id="bad", result={"intent": "modify", "targets": ["nope"],
                                                "hard": False, "confidence": 0.9})
    assert not r["ok"] and "bad_target" in r["error"]


def test_deliver_dedupe():
    s = Session(brief())
    s.deliver([asset(1)])
    r = s.deliver([asset(1), asset(2)])
    assert r["skipped"] and len(r["added"]) == 1, r
    assert len(s.delivered) == 2


def test_max_rounds():
    s = Session(brief(), max_rounds=2)
    s.interrupt("要正脸", msg_id="m5"); s.checkpoint()
    s.interrupt("要高清", msg_id="m6"); s.checkpoint()
    r = s.interrupt("再加两台", msg_id="m7")
    assert not r["ok"] and r["error"] == "max_rounds", r


def test_persistence_roundtrip():
    s = Session(brief())
    s.interrupt("要正脸", msg_id="m8"); s.checkpoint()
    s.deliver([asset(1)])
    raw = json.dumps(s.to_dict(), ensure_ascii=False)
    s2 = Session.from_dict(json.loads(raw))
    assert s2.version == s.version and s2.state == s.state
    assert len(s2.delivered) == 1 and s2.patches[0]["target"] == "fetch.filters.views"


def test_classifier_hard_scope():
    r = classify_text("只要精确的，不要邻近参考")
    assert r["hard"] and "scope.ratio" in r["targets"], r


def test_classifier_parts_vs_views():
    r = classify_text("重点看前脸格栅")
    assert "fetch.parts" in r["targets"] and "fetch.filters.views" not in r["targets"], r


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for name, fn in tests:
        check(name, fn)
    fails = [r for r in RESULTS if r[1] == "FAIL"]
    for name, status, err in RESULTS:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"session: {len(RESULTS) - len(fails)}/{len(RESULTS)} 通过")
    sys.exit(1 if fails else 0)
