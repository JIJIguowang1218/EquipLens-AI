# -*- coding: utf-8 -*-
"""候选规划核心测试（不联网、不调 LLM）。"""
import json
import re
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
    # 目标由用户输入推导：20 台 -> 1.6*(20+4)=39；抽取数按查询数反推
    lim = planning.auto_limits(20, 4, n_queries=6)
    assert lim["need"] == 39 and lim["limit"] == 39, lim
    # 12 台时上限保持 36（不因 need=26 而砍掉备选余量）
    assert planning.auto_limits(12, 4, n_queries=6)["limit"] == 36
    assert lim["per_query"] >= 8, lim
    assert planning.auto_limits(12, 4, n_queries=6)["need"] == 26


def test_short_query_builder():
    """长描述不能原样拼进搜索 query（2026-11-12 交付测试：0 结果/0 抽取）。"""
    from equiplens import planning
    b = {"request": {"class": "港口集装箱正面吊（reach stacker，集装箱正面吊运机）",
                     "configuration": "4×2 底盘",
                     "environment": {"value": "港口堆场，集装箱/潮湿盐雾，粉尘、车辆频繁起停、夜间强光作业"}},
         "research_units": [{"unit_id": "u-exact",
                             "scope": "港口集装箱正面吊（reach stacker） 4×2 底盘，用于堆场装卸"}],
         "negative": []}
    qs = planning.build_query_plan(b)
    assert qs, qs
    assert all("（" not in q["query"] and "(" not in q["query"] for q in qs), qs
    assert all(len(q["query"]) <= 40 for q in qs), [(q["query"], len(q["query"])) for q in qs]
    extras = planning.top_up_queries(b, [q["query"] for q in qs], max_extra=2)
    assert len(extras) == 2, extras
    assert all(e["dimension"] == "topup" for e in extras)
    # 已用过的查询不再重复生成
    assert planning.top_up_queries(b, [e["query"] for e in extras]) == []


def test_merge_rules_from_human_verdicts():
    """2026-11-12 人审（沙漠牵引车 14 张卡）后的合并规则：
    同款泛称合并、弱泛称丢弃、多码记录拆分。"""
    from equiplens.planning import merge_candidates
    cards = [
        ["TAZ4922 6×6 油田专用牵引车", "TAZ4922 6×6 油田牵引车", "TAZ4922 6×6油田牵引车"],
        ["6×6 全驱沙漠车（可改装油田专用车）"],
        ["H6066 6×6 特种运输车", "H6066 6×6特种运输车"],
        ["6×6 越野牵引头（460 马力）"],
        ["Zetros 4051 AS 6×6"],
        ["6×6全驱沙漠车"],                       # 人审：应与 #2 合并
        ["X3000 6×6沙漠越野车"],
        ["6×6长头油田卡车（TGS系列）"],
        ["6×6 越野牵引车头（460 马力）"],
        ["6×6 沙漠卡车（400 马力，25 吨级）"],
        ["ND5250TSMZ04 沙漠车"],
        ["6×6沙漠卡车"],                          # 人审：不该保留
        ["HF 8066（H6066）6×6 重型沙漠运输车"],   # 人审：应拆成 8066 / 6066
        ["东风 6×6 沙漠卡车（400 马力 25 吨级）"],
    ]
    items = []
    for i, vs in enumerate(cards):
        for j, m in enumerate(vs):
            items.append({"model": m, "sources": [f"https://e/{i}/{j}"],
                          "source_query_id": "q", "source_query": "x"})
    merged = merge_candidates(items)
    models = [c["model"] for c in merged]
    assert len(merged) == 10, models
    # #4/#9 只差一个“车”字 → 并成一台；#10/#14 差品牌前缀 → 并成一台
    assert len([c for c in merged if "460" in c["model"]]) == 1, models
    big = next(c for c in merged if "400" in c["model"] and "沙漠卡车" in c["model"])
    assert any("东风" in v for v in big["model_variants"]), big["model_variants"]
    # #6 并入 #2：同一个候选里出现两种写法
    two = next(c for c in merged if "可改装油田专用车" in c["model"])
    assert set(two["model_variants"]) == {
        "6×6 全驱沙漠车（可改装油田专用车）", "6×6全驱沙漠车"}, two["model_variants"]
    # 多码拆分：H6066 归 H6066，HF8066 独立
    h = next(c for c in merged if c["model"].startswith("H6066"))
    assert any("HF 8066" in v for v in h["model_variants"]), h["model_variants"]
    assert any(c["model"].startswith("HF 8066") for c in merged), models
    # 弱泛称不单独成候选（被并入 #10 或丢弃）
    assert "6×6沙漠卡车" not in models


def test_no_negative_is_suffix_only():
    """A/B 开关只去掉 -"短词" 后缀，查询文本其余部分逐字相同。"""
    from equiplens import planning
    b = brief()
    with_neg = planning.build_query_plan(b)
    without = planning.build_query_plan(b, use_negative=False)
    assert [q["query_id"] for q in with_neg] == [q["query_id"] for q in without]
    strip = re.compile(r' -"[^"]*"')
    for a, c in zip(with_neg, without):
        assert strip.sub("", a["query"]).strip() == c["query"].strip(), (a, c)
        assert "-" not in c["query"], c["query"]


def test_negative_terms_only_short_words():
    """negative 只允许短排除词；整句指令/元词会毁掉查询（2026-11-12 复现）。"""
    from equiplens import planning
    old = {"negative": ["客车", "SUV", "多车拼图", "内饰", "广告"]}
    assert planning.negative_terms(old) == ["客车", "SUV", "多车拼图", "内饰"]
    bad = {"negative": [
        "不引入具体品牌/型号或“同系列”作为设计理由。",
        "不分析用户未点名的进气格栅、后视镜",
        "模型", "客车"]}
    assert planning.negative_terms(bad) == ["客车"], planning.negative_terms(bad)


def test_search_key_survives_validation_and_merge():
    """抽取阶段给的 search_key 要能过校验、合并时优先保留带型号码的那条。"""
    meta = {"query_id": "q-base", "dimension": "base", "query": "沙漠牵引车"}
    rows, _ = planning.validate_extraction(
        {"candidates": [{"model": "TAZ4922 6×6 油田牵引车", "sources": ["https://ok/1"],
                         "search_key": "TAZ4922 6x6"}]},
        {"https://ok/1"}, meta, limit=6)
    assert rows[0]["search_key"] == "TAZ4922 6x6", rows
    a = {"model": "豪沃 6×6 牵引车", "sources": ["u1"], "source_query": "q1",
         "source_query_id": "q-base", "dimension": "base",
         "search_key": "豪沃 6x6"}
    b = {"model": "豪沃 6×6 牵引车（ZZ4257）", "sources": ["u2"], "source_query": "q2",
         "source_query_id": "q-model", "dimension": "model",
         "search_key": "ZZ4257 6x6"}
    merged = planning.merge_candidates([a, b])
    assert len(merged) == 1, merged
    assert "ZZ4257" in merged[0]["search_key"], merged[0]


if __name__ == "__main__":
    check("查询计划：维度与 query_id", test_query_plan_dimensions)
    check("查询计划：extra/去重", test_query_plan_extra_and_dedupe)
    check("长负词不进 query", test_long_negative_not_in_query)
    check("A/B：no-negative 只去后缀", test_no_negative_is_suffix_only)
    check("查询计划：构型不重复", test_config_not_duplicated_in_unit_scope)
    check("抽取校验：拒绝跨查询 URL", test_validate_rejects_foreign_urls)
    check("候选归并：保留来源", test_merge_keeps_provenance)
    check("车型身份：同款合并/同品牌不并", test_model_identity_not_brand)
    check("候选归并：只并同款", test_merge_dedupes_same_model_only)
    check("覆盖报告：缺口/国际", test_coverage_reports_missing_and_intl)
    check("候选池下限守卫", test_pool_requirement_guard)
    check("查询压缩与补查询", test_short_query_builder)
    check("人审后的合并规则", test_merge_rules_from_human_verdicts)
    check("negative 只收短词", test_negative_terms_only_short_words)
    check("search_key 过校验/合并", test_search_key_survives_validation_and_merge)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"planning: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
