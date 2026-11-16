# -*- coding: utf-8 -*-
"""交付清单透明化（S3-03 + S3-05）：出处 / 证据等级 / 边界与缺口。

离线测试，用仓库内真实 run 作为夹具（state.json + summary.json 即可，
不依赖 images/：该目录 gitignore，换机器会缺）。
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

spec = importlib.util.spec_from_file_location(
    "build_delivery_manifest", ROOT / "scripts" / "build_delivery_manifest.py")
man = importlib.util.module_from_spec(spec)
spec.loader.exec_module(man)

RUN = ROOT / "data-test" / "runs" / "verify-yield3-20261112"
BRIEF = ROOT / "data-test" / "evals" / "task-briefs-20261109" / "brief-m1-desert.json"
PLAN = ROOT / "data-test" / "runs" / "plan-ab4-20261111" / "A2" / "plan-ranked.json"
GRADES = {"accepted", "probable", "unknown", "degraded"}

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:200]))


def _manifest():
    m = man.build_manifest(RUN, BRIEF, PLAN)
    assert m["user_delivery"]["delivered"], "fixture 没有交付车型"
    return m


def test_new_fields_exist():
    m = _manifest()
    rows = m["user_delivery"]["delivered"]
    for row in rows:
        # 老 run / 缺 asset_meta 时 source_url 退化为空串，这里只校验结构。
        assert isinstance(row.get("source_url"), str), row
        assert row.get("evidence_grade") in GRADES, row
    with_url = [r for r in rows if r["source_url"]]
    if with_url:
        assert all(r["source_url"].startswith(("http://", "https://"))
                   for r in with_url), "source_url 必须是 http(s) 或空串"
    else:
        # 夹具若换了没有 url 的 run，按设计降级为空串，不伪造出处。
        print("  [info] 夹具没有 source_url，已按空串降级")


def test_backward_compatible_fields():
    m = _manifest()
    for key in ("run_id", "state", "generated_from", "brief",
                "user_delivery", "monitoring", "reusable"):
        assert key in m, key
    for row in m["user_delivery"]["delivered"]:
        for key in ("model", "unit", "role", "intent_rank",
                    "degraded", "citation_only", "images"):
            assert key in row, key
    for row in m["user_delivery"]["backup"]:
        assert "images" in row and "model" in row, row


def test_missing_evidence_degrades():
    # 没有 asset_meta / verifications 时：出处空串、等级 unknown，不伪造、不抛异常。
    state = {"assets": {"t1": {"part": ["a1"]}},
             "verifications": {}, "asset_meta": {}}
    chosen = man._chosen_asset(state, "t1")
    assert chosen is not None
    assert man._source_url(chosen) == ""
    assert man._source_url(None) == ""
    assert man._evidence_grade(state, "t1", chosen) == "unknown"


def test_boundary_section_renders():
    m = _manifest()
    md = man.render_md(m)
    s = m["user_delivery"]["summary"]
    assert "### 边界与缺口" in md, md[:500]
    assert f"- degraded：{s.get('degraded')} 台" in md, md
    assert f"- citation_only：{s.get('citation_only')} 台" in md, md
    assert "- 无图交付车型：" in md, md
    # summary.delivery.unavailable 存在时才渲染归因；不在时不要编造。
    if m["monitoring"]["unavailable"]:
        assert "缺图归因（summary.delivery.unavailable）：" in md, md
    # 新表格列
    assert "| 出处 | 证据等级 |" in md, md[:500]


def test_old_manifest_still_renders():
    # 模拟旧版 DELIVERY.json：没有两个新字段、没有 unavailable。
    m = _manifest()
    for row in m["user_delivery"]["delivered"]:
        row.pop("source_url", None)
        row.pop("evidence_grade", None)
    for row in m["user_delivery"]["backup"]:
        row.pop("source_url", None)
        row.pop("evidence_grade", None)
    m["monitoring"]["unavailable"] = []
    md = man.render_md(m)
    for title in ("一、用户交付物", "二、内部监控", "三、可复用中间产物"):
        assert title in md, title
    assert "### 边界与缺口" in md, md
    assert "缺图归因（summary.delivery.unavailable）" not in md, "缺字段时不应渲染归因"


if __name__ == "__main__":
    check("新字段 source_url / evidence_grade", test_new_fields_exist)
    check("旧字段向后兼容", test_backward_compatible_fields)
    check("缺证据时降级为空", test_missing_evidence_degrades)
    check("边界与缺口渲染", test_boundary_section_renders)
    check("旧清单仍可渲染", test_old_manifest_still_renders)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"manifest: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
