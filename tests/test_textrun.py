"""textrun 测试：schema/预算/档案/段落分级/逃生口/运行日志（全离线）。"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import passage, runlog, strategy, textrun  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:160]))


INTENT = {
    "task_type": "text_design_scan",
    "category": "随车吊",
    "models": ["徐工 G系列"],
    "target_content": "design_analysis",
    "budget": {"max_queries": 8, "max_fetch": 6, "max_rounds": 2},
}

REGISTRY = {"sources": [{"domain": "360che.com", "trust": "high"}],
            "preferred_domains": ["360che.com"],
            "source_targeting": "site",
            "negative_terms": ["油耗", "报价"]}


def test_schema_validation():
    textrun.validate(INTENT, "intent.schema.json")
    plan = textrun.build_plan(INTENT, profile_name=None, profile=None,
                              registry=REGISTRY)
    textrun.validate(plan, "text-plan.schema.json")
    assert plan["profile_status"] == "missing"
    assert sum(plan["quota"].values()) <= 6
    assert len([q for qs in plan["queries"].values() for q in qs]) <= 8
    assert "随车吊" in plan["relevant_terms"]


def test_profile_resolution_and_ambiguity():
    profiles = textrun.load_profiles()
    name, prof = textrun.resolve_profile("重卡", profiles)
    assert name == "重卡" and prof
    # 翻斗铲车同时命中自卸车与装载机 → 不应擅自解析，必须走澄清
    name2, prof2 = textrun.resolve_profile("翻斗铲车", profiles)
    assert name2 is None and prof2 is None
    assert textrun.ambiguity_unresolved({}, "翻斗铲车", profiles) is True
    intent = {"ambiguities": [{"term": "翻斗铲车",
                               "options": ["自卸车", "装载机"],
                               "needs_confirmation": True}]}
    assert textrun.ambiguity_unresolved(intent, "重卡", profiles) is True
    # 明确给出车型时不再阻塞（批量运行场景）
    assert textrun.ambiguity_unresolved({"models": ["汕德卡C9H"]},
                                        "翻斗铲车", profiles) is False


def test_profile_plan_and_budget():
    profiles = textrun.load_profiles()
    name, prof = textrun.resolve_profile("重卡", profiles)
    plan = textrun.build_plan(
        {"task_type": "text_design_scan", "category": "重卡",
         "models": ["汕德卡C9H"], "target_content": "design_analysis",
         "budget": {"max_queries": 3, "max_fetch": 2, "max_rounds": 2}},
        profile_name=name, profile=prof, registry=REGISTRY)
    assert plan["profile_status"] == "found"
    assert len([q for qs in plan["queries"].values() for q in qs]) <= 3
    assert sum(plan["quota"].values()) <= 2
    assert any("重卡" in q for qs in plan["queries"].values() for q in qs)
    assert any(q.startswith("site:") for qs in plan["queries"].values()
               for q in qs), "定向查询不应被预算截断挤掉"


def test_passage_grading():
    body = """
[登录](https://x.com/login) [注册](https://x.com/reg) [首页](https://x.com/)
![图](https://x.com/a.jpg)
前脸采用V字形格栅，线条硬朗，镀铬饰条贯穿，营造出强烈的力量感与家族化识别。
发动机620马力，变速箱14档，油耗25升，报价40万，经销商优惠促销。
"""
    g = passage.grade_text(body, "high")
    assert g["a_count"] >= 1, g
    assert g["a_chars"] > 0
    labels = [p["label"] for p in g["passages"]]
    assert "A" in labels and "C" in labels, labels


def test_grade_batch():
    tmp = Path(tempfile.mkdtemp())
    try:
        batch = tmp / "batch-x"
        batch.mkdir()
        doc = batch / "001-test.md"
        doc.write_text(
            "---\nurl: https://www.360che.com/a\ntitle: t\n---\n\n"
            "前脸采用V字形格栅，线条硬朗，镀铬饰条贯穿，营造出力量感。\n"
            "发动机620马力，油耗25升，报价40万。\n", encoding="utf-8")
        (batch / "index.json").write_text(json.dumps({
            "batch_id": "batch-x",
            "index": [{"url": "https://www.360che.com/a", "title": "t",
                       "source_type": "review", "status": "saved",
                       "file": "001-test.md", "chars": 100,
                       "query": "q"}]}, ensure_ascii=False), encoding="utf-8")
        rep = passage.grade_batch(batch, REGISTRY)
        assert rep["metrics"]["articles"] == 1
        assert rep["metrics"]["articles_with_a"] == 1
        assert rep["metrics"]["a_chars"] > 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_strategy_escape_hatch():
    good = {"articles": 5, "a_share": 0.12, "a_chars": 500,
            "source_types": ["industry", "review"], "failed": 0}
    assert strategy.assess(good)["action"] == "ok"
    bad = {"articles": 1, "a_share": 0.01, "a_chars": 20,
           "source_types": ["industry"], "failed": 0}
    d = strategy.assess(bad, round_no=1, max_rounds=2)
    assert d["action"] == "replan" and "expand_design_queries" in d["scope"]
    d2 = strategy.assess(bad, round_no=2, max_rounds=2)
    assert d2["action"] == "stop"
    d3 = strategy.assess(bad, ambiguity_unresolved=True)
    assert d3["action"] == "ask_user"
    d4 = strategy.assess(bad, profile_status="missing")
    assert "propose_profile" in d4["scope"]
    # 政策跳过（blocked_url/source_skipped）不算硬失败，不应误判为低信度
    policy = {"articles": 4, "a_share": 0.07, "a_chars": 700,
              "source_types": ["industry", "review"],
              "failed": 12, "hard_failed": 0}
    assert strategy.assess(policy)["action"] == "ok"


def test_runlog_trace():
    tmp = Path(tempfile.mkdtemp())
    try:
        log = runlog.RunLog(tmp, "run-test", meta={"x": 1})
        with log.stage("plan"):
            log.tool("noop", args={"a": 1}, result={"ok": True}, duration_ms=1.2)
            log.llm("assistant-manual", "v0", input_text="你好世界",
                    output_text="计划")
        log.decision("ok", "达标")
        out = log.finish(summary={"status": "ok"}, metrics={"a": 1})
        assert (log.dir / "events.jsonl").exists()
        assert (log.dir / "summary.json").exists()
        assert out["stages"][0]["status"] == "ok"
        assert out["tools"][0]["name"] == "noop"
        assert out["token_estimate"]["input"] >= 1
        events = (log.dir / "events.jsonl").read_text(encoding="utf-8")
        for ev in ("run_start", "stage_start", "tool_call", "llm_call",
                   "decision", "stage_end", "run_end"):
            assert ev in events, ev
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_budget_binding():
    profiles = textrun.load_profiles()
    name, prof = textrun.resolve_profile("重卡", profiles)
    intent = {"task_type": "text_design_scan", "category": "重卡",
              "models": ["汕德卡C9H"], "target_content": "design_analysis",
              "budget": {"max_queries": 10, "max_fetch": 12, "max_rounds": 2}}
    plan = textrun.build_plan(intent, profile_name=name, profile=prof,
                              registry=REGISTRY)
    assert sum(plan["quota"].values()) == 12, plan["quota"]
    intent2 = dict(intent, budget={"max_queries": 10, "max_fetch": 20,
                                   "max_rounds": 2, "per_type_quota": 2})
    plan2 = textrun.build_plan(intent2, profile_name=name, profile=prof,
                               registry=REGISTRY)
    assert sum(plan2["quota"].values()) == 4, plan2["quota"]
    # SERP 渠道可配置；默认 auto（百度被拦时退 Bing）
    assert plan.get("serp_channel") == "auto"
    assert plan["budget"]["per_type_quota"] == 6


def test_config_line_filter():
    """报价配置行必须判 C（T18-roster：'高顶'误命中维度词导致 B 档穿透）。"""
    cfg = "2022款 2.0T柴油商运版长轴高顶厢货2座D20TCIF1"
    assert passage.score_passage(cfg, "medium")["label"] == "C", cfg
    ok = "前脸采用V字形格栅，线条硬朗，镀铬饰条贯穿，营造出强烈的力量感与家族化识别。"
    assert passage.score_passage(ok, "high")["label"] in ("A", "B")


def test_query_meta_groups():
    """查询分层：车型查询与类目查询的 relevant_terms 必须不同。"""
    profiles = textrun.load_profiles()
    name, prof = textrun.resolve_profile("重卡", profiles)
    plan = textrun.build_plan(
        {"task_type": "text_design_scan", "category": "重卡",
         "models": ["汕德卡C9H"], "target_content": "design_analysis",
         "budget": {"max_queries": 20, "max_fetch": 12, "max_rounds": 2}},
        profile_name=name, profile=prof, registry=REGISTRY)
    metas = plan["query_meta"]
    assert metas, metas
    vehicle = [q for q, m in metas.items() if m["info_type"] == "vehicle"]
    assert vehicle and "汕德卡C9H" in vehicle[0], vehicle
    macro = [q for q, m in metas.items() if m["info_type"] == "macro"]
    assert macro, metas
    m_terms = metas[macro[0]]["relevant_terms"]
    assert any(w in t for t in m_terms for w in ("造型", "设计语言", "工业设计")), m_terms
    v_terms = metas[vehicle[0]]["relevant_terms"]
    assert "汕德卡C9H" in v_terms, v_terms


if __name__ == "__main__":
    check("intent/plan schema 与预算", test_schema_validation)
    check("类目档案解析与歧义", test_profile_resolution_and_ambiguity)
    check("有档案计划与预算帽", test_profile_plan_and_budget)
    check("预算上限真正生效（max_fetch/per_type）", test_budget_binding)
    check("段落清洗与 A/C 分级", test_passage_grading)
    check("报价配置行判 C", test_config_line_filter)
    check("查询分层 query_meta", test_query_meta_groups)
    check("批次评估汇总", test_grade_batch)
    check("低信度逃生口决策", test_strategy_escape_hatch)
    check("运行日志事件与摘要", test_runlog_trace)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"textrun: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
