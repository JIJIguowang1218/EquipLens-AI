# -*- coding: utf-8 -*-
"""候选规划核心测试（不联网、不调 LLM）。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens import planning  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:200]))


def brief():
    return json.loads((ROOT / "data-test" / "evals" / "task-briefs-20261109"
                       / "brief-m1-desert.json").read_text(encoding="utf-8"))


def test_query_plan_dimensions():
    plan = planning.build_query_plan(brief())
    dims = [q["dimension"] for q in plan]
    assert dims[:4] == ["base", "model", "environment", "english"], dims
    assert dims.count("unit") == 2, dims
    assert len({q["query_id"] for q in plan}) == len(plan), plan
    assert all('"' in q["query"] for q in plan), plan  # 负词已追加


def test_long_negative_not_in_query():
    b = brief()
    b["negative"] = ["不要把前脸自行拆成格栅、大灯、保险杠等用户未点名的子部件。",
                     "客车"]
    plan = planning.build_query_plan(b)
    assert all("不要把" not in q["query"] for q in plan), plan
    assert all('"客车"' in q["query"] for q in plan), plan


def test_query_plan_extra_and_dedupe():
    plan = planning.build_query_plan(brief(), ["进口 沙漠牵引车 6×6 车型",
                                               "进口 沙漠牵引车 6×6 车型"])
    extras = [q for q in plan if q["dimension"] == "extra"]
    assert len(extras) == 1 and extras[0]["query_id"] == "q-extra-1", extras
    # 重复查询只保留第一次
    texts = [q["query"] for q in plan]
    assert len(texts) == len(set(texts)), texts


def test_config_not_duplicated_in_unit_scope():
    plan = planning.build_query_plan(brief())
    unit = [q for q in plan if q["dimension"] == "unit"][0]
    assert "6×6 6×6" not in unit["query"], unit


def test_validate_rejects_foreign_urls():
    meta = {"query_id": "q-model", "dimension": "model",
            "query": "沙漠牵引车 6×6 车型 品牌"}
    payload = {"candidates": [
        {"model": "A", "sources": ["https://ok/1"]},
        {"model": "B", "sources": ["https://bad/2"]},
        {"model": "A", "sources": ["https://ok/3"]},
        {"model": "C", "sources": ["https://ok/4", "https://bad/5"]},
    ]}
    rows, stats = planning.validate_extraction(
        payload, {"https://ok/1", "https://ok/4"}, meta, limit=6)
    assert [r["model"] for r in rows] == ["A", "C"], rows
    assert stats["dropped_no_source"] == 1, stats
    assert stats["dropped_invalid_source"] == 2, stats
    assert rows[0]["source_query"] == meta["query"], rows[0]


def test_merge_keeps_provenance():
    a = {"model": "Zetros 4051", "sources": ["u1"], "source_query": "q1",
         "source_query_id": "q-model", "dimension": "model"}
    b = {"model": "zetros 4051", "sources": ["u2"], "source_query": "q2",
         "source_query_id": "q-extra-1", "dimension": "extra"}
    merged = planning.merge_candidates([a, b])
    assert len(merged) == 1, merged
    assert merged[0]["sources"] == ["u1", "u2"], merged[0]
    assert merged[0]["dimensions"] == ["model", "extra"], merged[0]
    assert len(merged[0]["source_queries"]) == 2, merged[0]


def test_model_identity_not_brand():
    """同款变体合并，但同品牌不同型号必须分开（品牌不是去重单位）。"""
    taz = [
        "豪沃 TAZ4922 6×6 油田专用牵引车",
        "豪沃(HOWO) 6×6 油田专用牵引车 TAZ4922（泰安五岳）",
        "豪沃 6×6 油田专用牵引车（泰安五岳 TAZ4922）",
    ]
    assert len({planning.model_identity(m) for m in taz}) == 1
    assert planning.model_identity("Zetros 4051 AS 6×6") != \
        planning.model_identity("Zetros 3643 6×6")
    assert planning.model_identity("东风 EQ2251AX") != \
        planning.model_identity("东风 EQ2220AX")
    assert planning.model_identity("DFV5253TSMGP6D") != \
        planning.model_identity("DFV2223GP6DJ")
    # 泛称不与具体型号码硬并
    assert planning.model_identity("6×6 越野牵引头（460马力）")[0] == "generic"
    assert planning.model_identity("TAZ4922 6×6")[0] == "code"
    # GVW/HP 等参数不是型号码
    assert planning.model_identity("K-65959（6×6，GVW 35000 kg）") == \
        planning.model_identity("K-65959 6×6")


def test_merge_dedupes_same_model_only():
    items = [
        {"model": "TAZ4922 6×6", "sources": ["u1"], "source_query": "q1",
         "source_query_id": "q1", "dimension": "model"},
        {"model": "豪沃 TAZ4922 6×6 油田牵引车", "sources": ["u2"],
         "source_query": "q2", "source_query_id": "q2", "dimension": "unit"},
        {"model": "Zetros 4051 AS", "sources": ["u3"], "source_query": "q1",
         "source_query_id": "q1", "dimension": "model"},
        {"model": "Zetros 3643", "sources": ["u4"], "source_query": "q1",
         "source_query_id": "q1", "dimension": "model"},
        {"model": "EQ2251AX", "sources": ["u5"], "source_query": "q1",
         "source_query_id": "q1", "dimension": "model"},
        {"model": "EQ2220AX", "sources": ["u6"], "source_query": "q1",
         "source_query_id": "q1", "dimension": "model"},
    ]
    merged = planning.merge_candidates(items)
    models = {m["identity"] for m in merged}
    assert len(merged) == 5, [m["model"] for m in merged]
    assert len(models) == 5
    taz = next(m for m in merged if m["identity_kind"] == "code")
    assert len(taz["model_variants"]) == 2 and len(taz["sources"]) == 2, taz
    stats = planning.dedupe_stats(items, merged)
    assert stats["input"] == 6 and stats["unique"] == 5 and stats["removed"] == 1, stats


def test_coverage_reports_missing_and_intl():
    plan = planning.build_query_plan(brief(), ["进口 沙漠牵引车 6×6 车型"])
    cands = [{"dimensions": ["model"], "source_query": "沙漠牵引车 6×6 车型 品牌"},
             {"dimensions": ["extra"], "source_query": "进口 沙漠牵引车 6×6 车型"}]
    cov = planning.coverage_report(plan, cands)
    assert cov["dimensions"]["model"]["candidates"] == 1, cov
    assert "base" in cov["missing"], cov
    assert cov["international_covered"] is True, cov


def test_pool_requirement_guard():
    """候选池下限：1.6×(slots+backup)；12 主 + 4 备 => 26。"""
    from equiplens import planning
    assert planning.pool_requirement(12, 4) == 26, planning.pool_requirement(12, 4)
    assert planning.pool_requirement(8, 4) == 20
    assert planning.pool_requirement(0, 4) == 0
    assert planning.pool_warning(26, 12, 4) == ""
    assert "26" in planning.pool_warning(20, 12, 4)


if __name__ == "__main__":
    check("查询计划：维度与 query_id", test_query_plan_dimensions)
    check("查询计划：extra/去重", test_query_plan_extra_and_dedupe)
    check("长负词不进 query", test_long_negative_not_in_query)
    check("查询计划：构型不重复", test_config_not_duplicated_in_unit_scope)
    check("抽取校验：拒绝跨查询 URL", test_validate_rejects_foreign_urls)
    check("候选归并：保留来源", test_merge_keeps_provenance)
    check("车型身份：同款合并/同品牌不并", test_model_identity_not_brand)
    check("候选归并：只并同款", test_merge_dedupes_same_model_only)
    check("覆盖报告：缺口/国际", test_coverage_reports_missing_and_intl)
    check("候选池下限守卫", test_pool_requirement_guard)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"planning: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
