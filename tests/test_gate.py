# -*- coding: utf-8 -*-
"""门卫分层判定测试（离线；不加载 CLIP，全部用假结果拼装）。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import gate  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:160]))


def gate_pass(scene="single_vehicle"):
    return {"pass": True, "keep": 0.30, "drop": 0.26, "margin": 0.04,
            "scene": scene, "keep_label": "single truck",
            "drop_label": "lineup"}


def gate_drop():
    return {"pass": False, "keep": 0.20, "drop": 0.30, "margin": -0.10,
            "scene": None, "keep_label": "single truck",
            "drop_label": "collage"}


def view(name="front", gap=0.0004):
    return {"view": name, "score": 0.29, "gap": gap,
            "scores": {name: 0.29}}


def assess(gate_result, view_result, width=1700, height=1000):
    return gate.assess_from_gate(gate_result, view_result, width, height)


def test_drop_labels_cover_smoke_failures():
    """v3 四个反例必须在 DROP_LABELS 里（W1 冒烟暴露的漏网类型）。"""
    joined = " | ".join(gate.DROP_LABELS).lower()
    for needle in ("interior cabin", "collage", "screenshot", "advertisement"):
        assert needle in joined, f"missing drop label: {needle}"


def test_assess_part_and_overview_tiers():
    a = assess(gate_pass(), view("front", gap=0.02), 1700, 1000)
    assert a["part_candidate"] and a["overview_candidate"], a
    assert a["exterior_hint"] and a["view_trusted"], a
    assert a["reasons"] == [] and a["hints"] == [], a

    # 900px：概览可用，部件不可用
    a = assess(gate_pass(), view(), 900, 600)
    assert a["overview_candidate"] and not a["part_candidate"], a
    assert "low_res_part" in a["reasons"], a["reasons"]

    # 500px：两层都不可用
    a = assess(gate_pass(), view(), 500, 400)
    assert not a["overview_candidate"] and not a["part_candidate"], a
    assert "low_res_overview" in a["reasons"], a["reasons"]


def test_assess_gate_drop_and_multi_vehicle():
    a = assess(gate_drop(), view(), 1700, 1000)
    assert not a["overview_candidate"] and not a["part_candidate"], a
    assert "gate_drop" in a["reasons"], a["reasons"]
    assert not a["exterior_hint"], a

    # v4：scene=multi 不再一刀切否决，但也不占概览/部件名额，只进参考层
    a = assess(gate_pass("multi_vehicle"), view(), 1700, 1000)
    assert not a["overview_candidate"] and not a["part_candidate"], a
    assert a["reference_candidate"], a
    assert "multi_vehicle" not in a["reasons"], a["reasons"]
    assert "background_vehicles" in a["hints"], a["hints"]
    assert a["multi_vehicle"], a


def test_view_is_hint_not_veto():
    """视角=detail 不能否决部件可用；top1−top2 小只能标 view_uncertain。"""
    a = assess(gate_pass(), view("detail", gap=0.0026), 1700, 1000)
    assert a["part_candidate"], a
    assert not a["exterior_hint"], a
    assert "view_detail_hint" in a["hints"], a["hints"]
    assert not a["view_trusted"], a

    # 正视角但 gap 极小：仍是可用候选，只是提示不可信
    a = assess(gate_pass(), view("front", gap=0.0004), 1707, 1280)
    assert a["part_candidate"] and a["exterior_hint"], a
    assert not a["view_trusted"], a
    assert "view_uncertain" in a["hints"], a["hints"]


def test_interior_strong_signal_only():
    """interior 只在 gap ≥ 0.01 时当强信号否决；弱信号不否决（避免误杀）。"""
    strong = assess(gate_pass(), view("interior", gap=0.0221), 800, 533)
    assert not strong["part_candidate"] and not strong["overview_candidate"], strong
    assert strong["interior_suspect"], strong
    assert "interior_suspect" in strong["reasons"], strong["reasons"]

    weak = assess(gate_pass(), view("interior", gap=0.0032), 1200, 800)
    assert weak["overview_candidate"] and weak["part_candidate"], weak
    assert not weak["interior_suspect"], weak


def test_assess_image_wires_check_and_view():
    """assess_image = 预筛 → check → classify_view → 分层（真实尺寸取自预筛）。"""
    op, og, ov = gate.prefilter, gate.check, gate.classify_view
    gate.prefilter = lambda data: {
        "ok": True, "stage": "prefilter", "reasons": [], "bytes": len(data),
        "format": "jpeg", "width": 1705, "height": 1280, "long_side": 1705,
        "short_side": 1280, "aspect": 1.332, "pixels": 1705 * 1280,
        "animated": False, "std": 41.0, "ms": 1.0}
    gate.check = lambda data, *a, **k: gate_pass()
    gate.classify_view = lambda data: view("front", gap=0.0004)
    try:
        a = gate.assess_image(b"x")
        assert a["part_candidate"] and a["width"] == 1705, a
        assert a["exterior_hint"] and not a["view_trusted"], a
        assert a["stage"] == "gate" and not a["gate_skipped"], a
    finally:
        gate.prefilter, gate.check, gate.classify_view = op, og, ov


def _img_bytes(w, h, color=(120, 130, 140)):
    import io as _io

    from PIL import Image
    buf = _io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, "PNG")
    return buf.getvalue()


def _gradient_bytes(w, h):
    import io as _io

    from PIL import Image
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(0, w, 4):   # 4px 步进够撑开灰度标准差
            px[x, y] = ((x * 7) % 256, (y * 5) % 256, ((x + y) * 3) % 256)
    buf = _io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return buf.getvalue()


def test_prefilter_catches_only_hard_facts():
    """第一段只挡硬事实：明显过小 / 近空白 / banner / 破图。"""
    p = gate.prefilter(_img_bytes(200, 200))
    assert not p["ok"] and "too_small" in p["reasons"], p

    p = gate.prefilter(_img_bytes(1600, 1000))       # 纯色 1600×1000
    assert not p["ok"] and "near_uniform" in p["reasons"], p

    p = gate.prefilter(_gradient_bytes(2000, 300))   # 长宽比 6.7
    assert not p["ok"] and "extreme_aspect" in p["reasons"], p

    p = gate.prefilter(b"not-an-image")
    assert not p["ok"] and "undecodable" in p["reasons"], p

    # 640×480 / 360×240 的真车图必须过第一段（800 是“可用”门槛，不是“存在”门槛）
    p = gate.prefilter(_gradient_bytes(640, 480))
    assert p["ok"], p
    assert p["long_side"] == 640, p

    p = gate.prefilter(_gradient_bytes(360, 240))
    assert p["ok"], p

    p = gate.prefilter(_gradient_bytes(1700, 1000))
    assert p["ok"] and p["reasons"] == [], p
    assert p["long_side"] == 1700 and p["aspect"] == 1.7, p
    assert p["std"] and p["std"] > gate.PREFILTER_MIN_STD, p


def test_prefilter_blocks_before_clip():
    """预筛失败时 assess_image 不跑 CLIP（gate_skipped=True）。"""
    op, og = gate.prefilter, gate.check

    def boom(*a, **k):  # 一旦被调用说明两段式没生效
        raise AssertionError("CLIP 不该在预筛已否决时运行")

    gate.prefilter = lambda data: {
        "ok": False, "stage": "prefilter", "reasons": ["too_small"],
        "bytes": len(data), "format": "png", "width": 200, "height": 200,
        "long_side": 200, "short_side": 200, "aspect": 1.0, "pixels": 40000,
        "animated": False, "std": 30.0, "ms": 0.5}
    gate.check = boom
    try:
        a = gate.assess_image(b"x")
        assert a["stage"] == "prefilter" and a["gate_skipped"], a
        assert a["reasons"] == ["too_small"], a
        assert not a["overview_candidate"] and not a["part_candidate"], a
        # 已算好的门卫结果 + 预筛失败 → 同样被拦（不信任上游"通过"）
        a = gate.assess_from_gate(gate_pass(), view("front", gap=0.02),
                                  1700, 1000,
                                  prefilter_result={"ok": False,
                                                    "reasons": ["too_small"]})
        assert a["stage"] == "prefilter" and not a["overview_candidate"], a
    finally:
        gate.prefilter, gate.check = op, og


def test_reference_tier_for_low_res():
    """低清但语义可用 → 参考层（可看不可用），不占概览/部件名额。"""
    a = assess(gate_pass(), view("detail", gap=0.02), 640, 480)
    assert not a["overview_candidate"] and not a["part_candidate"], a
    assert a["reference_candidate"], a
    assert "low_res_overview" in a["reasons"], a["reasons"]

    # T33 起 `reference_candidate` 的语义是“过门卫即可参考”，不再是“低清专属”；
    # 900×600 既是概览图也在参考层（字段是标签，不是互斥筛选器）。
    a = assess(gate_pass(), view("front", gap=0.02), 900, 600)
    assert a["overview_candidate"] and a["reference_candidate"], a


def test_label_sets_sizes():
    """v3 在 v2 的 7 条反例上再加 4 条；v4 再加 1 条 keep；check_v2 用 7 条。"""
    assert len(gate.BASE_DROP_LABELS) == 7, gate.BASE_DROP_LABELS
    assert len(gate.V3_DROP_LABELS) == 4, gate.V3_DROP_LABELS
    assert gate.DROP_LABELS == gate.BASE_DROP_LABELS + gate.V3_DROP_LABELS
    assert len(gate.KEEP_LABELS) == 4, gate.KEEP_LABELS
    assert gate.GATE_LABEL_VERSION == "v4"


def test_verification_roundtrip_keeps_warnings():
    from equiplens.retrieval_engine.contracts import Verification
    v = Verification(accepted=True, defects=(), warnings=("view_mismatch",))
    d = v.to_dict()
    assert d["warnings"] == ["view_mismatch"], d
    assert Verification.from_dict(d).warnings == ("view_mismatch",), d


if __name__ == "__main__":
    check("反例标签覆盖 W1 漏网类型", test_drop_labels_cover_smoke_failures)
    check("概览/部件两层口径", test_assess_part_and_overview_tiers)
    check("门卫拒绝与多车拼图", test_assess_gate_drop_and_multi_vehicle)
    check("视角只作提示不否决", test_view_is_hint_not_veto)
    check("内饰强信号才否决", test_interior_strong_signal_only)
    check("assess_image 接线", test_assess_image_wires_check_and_view)
    check("预筛只挡硬事实", test_prefilter_catches_only_hard_facts)
    check("预筛先于 CLIP（省推理）", test_prefilter_blocks_before_clip)
    check("低清图进参考层", test_reference_tier_for_low_res)
    check("v2/v3 标签集规模", test_label_sets_sizes)
    check("Verification 保留 warnings", test_verification_roundtrip_keeps_warnings)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"gate: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
