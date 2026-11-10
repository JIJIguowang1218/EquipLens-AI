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


def test_coverage_reports_missing_and_intl():
    plan = planning.build_query_plan(brief(), ["进口 沙漠牵引车 6×6 车型"])
    cands = [{"dimensions": ["model"], "source_query": "沙漠牵引车 6×6 车型 品牌"},
             {"dimensions": ["extra"], "source_query": "进口 沙漠牵引车 6×6 车型"}]
    cov = planning.coverage_report(plan, cands)
    assert cov["dimensions"]["model"]["candidates"] == 1, cov
    assert "base" in cov["missing"], cov
    assert cov["international_covered"] is True, cov


if __name__ == "__main__":
    check("查询计划：维度与 query_id", test_query_plan_dimensions)
    check("查询计划：extra/去重", test_query_plan_extra_and_dedupe)
    check("查询计划：构型不重复", test_config_not_duplicated_in_unit_scope)
    check("抽取校验：拒绝跨查询 URL", test_validate_rejects_foreign_urls)
    check("候选归并：保留来源", test_merge_keeps_provenance)
    check("覆盖报告：缺口/国际", test_coverage_reports_missing_and_intl)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"planning: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
