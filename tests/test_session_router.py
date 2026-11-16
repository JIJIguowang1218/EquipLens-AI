# -*- coding: utf-8 -*-
"""S0-05 Router（LLM 提议 + 守卫）单测；不联网。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens import session_router as R  # noqa: E402
from equiplens.session import Session, SessionState  # noqa: E402

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        RESULTS.append((name, "FAIL", str(e)[:200]))


def fake(payload, seen=None):
    def _chat(prompt, key, model):
        if seen is not None:
            seen["prompt"] = prompt
        return {"payload": payload, "usage": {}, "model": model}
    return _chat


def test_views():
    r = R.classify("全要正面", chat_fn=fake({"targets": ["fetch.filters.views"], "hard": False, "confidence": 0.9}))
    assert r["targets"] == [] and r["clarify"], r
    assert "更多这辆车" in (r.get("question") or ""), r


def test_invalid_target_clarifies():
    r = R.classify("随便", chat_fn=fake({"targets": ["nope"], "confidence": 0.9}))
    assert r["clarify"] and not r["targets"], r


def test_scope_plus_negative_keeps_hard():
    r = R.classify("只要精确，把北奔去掉",
                   chat_fn=fake({"targets": ["scope.ratio", "plan.negative"], "confidence": 0.9}))
    assert r["hard"] is True and r["enforce"] == "hard", r


def test_negative_enforce_hard_but_soft():
    r = R.classify("不要挂车", chat_fn=fake({"targets": ["plan.negative"], "hard": False, "confidence": 0.9}))
    assert r["targets"] == ["plan.negative"] and r["enforce"] == "hard" and r["hard"] is False, r


def test_quantity_hard():
    r = R.classify("数量加到 14 台", chat_fn=fake({"targets": ["plan.quantity"], "confidence": 0.9}))
    assert r["hard"] is True and r["targets"] == ["plan.quantity"], r


def test_clear_delete_no_confirm():
    r = R.classify("删掉第 2 张", chat_fn=fake({"targets": ["delivered.remove"], "destructive": True,
                                               "confirm": False, "confidence": 0.9}))
    assert r["destructive"] and r["confirm"] is False, r


def test_ambiguous_delete_confirms():
    r = R.classify("删掉一张", chat_fn=fake({"targets": ["delivered.remove"], "destructive": True,
                                            "confirm": True, "confidence": 0.9}))
    assert r["destructive"] and r["confirm"] is True, r


def test_reset_hard_confirm():
    r = R.classify("全部重来", chat_fn=fake({"targets": ["session.reset"], "hard": True,
                                            "destructive": True, "confirm": True, "confidence": 0.9}))
    assert r["hard"] and r["confirm"] and r["targets"] == ["session.reset"], r


def test_too_many_targets_clarify():
    r = R.classify("x", chat_fn=fake({"targets": ["fetch.filters.views", "fetch.filters.quality",
                                                 "fetch.parts", "fill.quota"], "confidence": 0.9}))
    assert r["clarify"], r


def test_low_confidence_clarify():
    r = R.classify("嗯", chat_fn=fake({"targets": ["fill.quota"], "confidence": 0.3}))
    assert r["clarify"], r


def test_context_in_prompt():
    seen = {}
    R.classify("同款再来三张", context={"targets": [{"model": "X3000"}]},
               chat_fn=fake({"targets": ["fill.quota"], "confidence": 0.9}, seen))
    assert "X3000" in seen["prompt"], "context 未进入 prompt"


def test_fallback_rules():
    def boom(prompt, key, model):
        raise RuntimeError("api down")
    r = R.classify("要正脸图", chat_fn=boom)
    assert r["targets"] == ["fetch.filters.views"], r


def test_make_router():
    r = R.make_router("", chat_fn=fake({"targets": ["fetch.filters.quality"], "confidence": 0.9}))
    out = r("要高清", {})
    assert out["targets"] == ["fetch.filters.quality"], out
    s = Session({"request": {"class": "沙漠牵引车"}}, router=r)
    res = s.interrupt("要高清", msg_id="mk1")
    assert res["ok"] and s.pending[0].target == "fetch.filters.quality", res


def test_session_uses_router():
    s = Session({"request": {"class": "沙漠牵引车", "page_budget": {"vehicle_slots": 10}}},
                router=lambda text, ctx: {"targets": ["fetch.filters.views"], "hard": False,
                                          "confidence": 0.9, "destructive": False, "confirm": False})
    r = s.interrupt("全要正面", msg_id="r1")
    assert r["ok"] and s.pending[0].target == "fetch.filters.views", r


def test_session_router_confirm():
    s = Session({"request": {"class": "沙漠牵引车"}},
                router=lambda text, ctx: {"targets": ["delivered.remove"], "hard": False,
                                          "destructive": True, "confirm": True, "confidence": 0.9})
    r = s.interrupt("删掉一张", msg_id="r2")
    assert r.get("clarify") and s.state == SessionState.CLARIFYING, r


def test_composite_targets_preserved():
    r = R.classify("驾驶室要高顶的，平顶的不要",
                   chat_fn=fake({"targets": ["plan.negative", "plan.configuration"],
                                 "confidence": 0.9}))
    assert set(r["targets"]) == {"plan.negative", "plan.configuration"}, r


def test_config_not_parts():
    r = R.guard("配置按沙漠版那种来，双备胎加涉水喉",
                {"targets": ["fetch.parts"], "confidence": 0.9})
    assert r["targets"] == ["plan.configuration"], r
    r2 = R.guard("要格栅和大灯的细节图", {"targets": ["fetch.parts"], "confidence": 0.9})
    assert r2["targets"] == [] and r2["clarify"], r2


def test_clarify_has_options():
    r = R.guard("嗯", {"targets": [], "confidence": 0.3})
    assert r["clarify"] and r["options"], r
    r2 = R.guard("删掉一张", {"targets": [], "confidence": 0.9})
    assert r2["clarify"] and r2["options"], r2


def test_report_not_per_model():
    r = R.guard("报告里每个车型配一张图就行",
                {"targets": ["plan.quantity_per_model"], "confidence": 0.9})
    assert r["targets"] == ["delivery.report"], r


def test_image_edit_not_configuration():
    r = R.guard("第4张是8x8的，我们要的是6x6，这张不能进",
                {"targets": ["delivered.remove", "plan.configuration"], "confidence": 0.9})
    assert r["targets"] == ["verify.blacklist"], r


def test_print_request_explained():
    r = R.guard("打印成海报行不行", {"targets": ["delivery.report"], "confidence": 0.9})
    assert r["targets"] == [] and r["action"] == "explain", r


def test_identity_config_image_blacklisted():
    r = R.guard("第4张是8x8，不是6x6",
                {"targets": ["plan.configuration"], "confidence": 0.9})
    assert r["targets"] == ["verify.blacklist"], r


def test_angle_parts_clarify():
    for text, target in (("要正脸", "fetch.filters.views"), ("大灯特写", "fetch.parts")):
        r = R.guard(text, {"targets": [target], "confidence": 0.9})
        assert r["targets"] == [] and r["action"] == "clarify", (text, r)
        assert "更多这辆车" in (r.get("question") or ""), r
    # 混合：角度 + 画质 → 保留画质，不产角度 patch
    r = R.guard("要正脸和高清", {"targets": ["fetch.filters.views", "fetch.filters.quality"],
                                 "confidence": 0.9})
    assert r["targets"] == ["fetch.filters.quality"], r


def test_negated_attribute_not_configuration():
    r = R.guard("别要右舵的", {"targets": ["plan.negative", "plan.configuration"],
                               "confidence": 0.9})
    assert r["targets"] == ["plan.negative"], r


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for name, fn in tests:
        check(name, fn)
    fails = [r for r in RESULTS if r[1] == "FAIL"]
    for name, status, err in RESULTS:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"session_router: {len(RESULTS) - len(fails)}/{len(RESULTS)} 通过")
    sys.exit(1 if fails else 0)
