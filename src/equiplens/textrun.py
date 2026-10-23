"""文本检索编排器：intent → 类目档案 → 查询计划 → 执行 → 段落评估 → 低信度重规划。

原则:
- 控制流固定（workflow），内容判断在 L1/L3/L4 的关节上。
- 锁定项（robots/配额/账本/检查点/schema）不可被模型绕过。
- 每次运行写 runs/<run_id>/events.jsonl + summary.json（时间/token 估算/工具/决策）。
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import jsonschema

from . import corpus, passage, runlog, strategy

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
DEFAULT_REGISTRY = ROOT / "data" / "source_registry.json"
DEFAULT_PROFILES = ROOT / "data" / "category_profiles.json"


def _load_json(path: Path | str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate(instance: dict, schema_name: str) -> None:
    schema = _load_json(SCHEMAS / schema_name)
    jsonschema.validate(instance=instance, schema=schema)


def load_registry(path: str | Path | None = None) -> dict:
    p = Path(path) if path else DEFAULT_REGISTRY
    return _load_json(p) if p.exists() else {"sources": [], "negative_terms": []}


def load_profiles(path: str | Path | None = None) -> dict:
    p = Path(path) if path else DEFAULT_PROFILES
    return _load_json(p) if p.exists() else {"profiles": {}}


def resolve_profile(category: str | None, profiles: dict) -> tuple[str | None, dict | None]:
    """精确名/别名匹配。返回 (档案名, 档案)；多个别名命中视为歧义。"""
    if not category:
        return None, None
    hits = []
    for name, prof in profiles.get("profiles", {}).items():
        terms = [name] + prof.get("aliases", [])
        if any(t and (t in category or category in t) for t in terms):
            hits.append((name, prof))
    if len(hits) == 1:
        return hits[0]
    return None, None


def ambiguity_unresolved(intent: dict, category: str | None, profiles: dict) -> bool:
    for a in intent.get("ambiguities", []):
        if a.get("needs_confirmation", True):
            return True
    if category:
        hits = []
        for name, prof in profiles.get("profiles", {}).items():
            terms = [name] + prof.get("aliases", [])
            if any(t and (t in category or category in t) for t in terms):
                hits.append(name)
        if len(hits) > 1:
            return True
    return False


def build_plan(intent: dict, *, profile_name: str | None, profile: dict | None,
               registry: dict, round_no: int = 1, suffix: str = "",
               wide: bool = False) -> dict:
    """由意图+档案生成受预算约束的查询计划。内容知识来自数据，不写进代码。"""
    budget = intent.get("budget", {})
    max_queries = int(budget.get("max_queries", 10))
    max_fetch = int(budget.get("max_fetch", 12))
    max_rounds = int(budget.get("max_rounds", 2))
    category = intent.get("category")
    models = intent.get("models", []) or []
    neg = list(dict.fromkeys(registry.get("negative_terms", [])))

    queries: dict[str, list[str]] = {}

    def add(q: str, st: str = "industry") -> None:
        q = q.strip()
        if not q:
            return
        bucket = queries.setdefault(st, [])
        if q not in bucket:
            bucket.append(q)

    # 1) 档案层：有档案时优先具体查询（预算截断时先保住类目相关）
    if profile:
        for alias in (profile.get("aliases") or [])[:2]:
            add(f"{alias} 造型 设计 语言", "industry")
        for model in models:
            add(f"{model} 外观 造型 设计 解读", "review")
        for comp in (profile.get("component_vocab") or [])[:4]:
            add(f"{category} {comp} 设计", "review")
        for term in (profile.get("market_terms") or [])[:2]:
            add(f"{term} 造型 设计 趋势", "industry")
    # 2) 通用层/宽搜轮：宽搜轮只跑“不同的”查询，避免重复上一轮
    if wide:
        for q in ["工程机械 工业设计", "特种车辆 外观 设计 解读",
                  "商用车 CMF 色彩 材质 趋势", "作业车 造型 设计"]:
            add(q, "industry")
        if category:
            add(f"{category} 驾驶室 设计", "review")
            add(f"{category} 工业设计 研究", "academic")
        add("专用车 造型 设计", "review")
        add("工程机械 造型设计 研究", "academic")
    else:
        for i, q in enumerate(strategy.generic_queries(category, models)):
            add(q, "industry" if i % 2 == 0 else "review")

    # 3) 预算：查询数上限
    flat = [(st, q) for st, qs in queries.items() for q in qs]
    if len(flat) > max_queries:
        flat = flat[:max_queries]
        queries = {}
        for st, q in flat:
            queries.setdefault(st, []).append(q)

    # 3) 配额：max_fetch 是真正的上限；per_type_quota 可显式覆盖
    types = list(queries)
    override = budget.get("per_type_quota")
    if override:
        per = max(1, int(override))
    else:
        per = max(1, max_fetch // max(1, len(types)))
    quota = {st: per for st in types}
    while sum(quota.values()) > max_fetch:
        st = max(quota, key=quota.get)
        if quota[st] <= 1:
            break
        quota[st] -= 1

    relevant = list(dict.fromkeys(
        [category] + (profile.get("aliases", []) if profile else [])
        + (profile.get("component_vocab", []) if profile else [])
        + models + ["工程机械", "商用车", "工程车辆", "驾驶室"]))
    relevant = [x for x in relevant if x]
    skip_domains = [
        s["domain"] for s in registry.get("sources", [])
        if s.get("trust") == "exclude"
        or s.get("design_yield") in ("none", "preview_only")]

    plan = {
        "batch_id": f"batch-text-{time.strftime('%Y%m%d-%H%M%S')}{suffix}",
        "purpose": intent.get("task_type", "text_design_scan"),
        "category": category,
        "models": models,
        "profile_ref": profile_name,
        "profile_status": (profile.get("status") or "found") if profile else "missing",
        "queries": queries,
        "quota": quota,
        "negative_terms": neg,
        "relevant_terms": relevant,
        "skip_domains": skip_domains,
        "serp_channel": intent.get("serp_channel", "auto"),
        "budget": {"max_queries": max_queries, "max_fetch": max_fetch,
                   "max_rounds": max_rounds, "per_type_quota": per},
        "round": round_no,
        "fallback": ["generic_layer", "switch_sources", "propose_profile"],
    }
    validate(plan, "text-plan.schema.json")
    return plan


def _merge_metrics(rounds: list[dict]) -> dict:
    docs = [d for r in rounds for d in r["grade"]["docs"]]
    total = sum(r["grade"]["metrics"]["total_chars"] for r in rounds)
    a = sum(r["grade"]["metrics"]["a_chars"] for r in rounds)
    failed = sum(r["grade"]["metrics"]["failed"] for r in rounds)
    return {
        "articles": len(docs),
        "articles_with_a": sum(1 for d in docs if d["a_count"] > 0),
        "total_chars": total,
        "a_chars": a,
        "b_chars": sum(r["grade"]["metrics"]["b_chars"] for r in rounds),
        "a_share": round(a / total, 4) if total else 0.0,
        "a_per_article": round(a / len(docs), 1) if docs else 0.0,
        "source_types": sorted({d["source_type"] for d in docs}),
        "serp_blocked_queries": sum(
            sum(1 for v in r.get("serp", {}).values() if v.get("blocked"))
            for r in rounds),
        "failed": failed,
        "hard_failed": sum(r["grade"]["metrics"].get("hard_failed", 0) for r in rounds),
        "policy_skipped": sum(r["grade"]["metrics"].get("policy_skipped", 0) for r in rounds),
        "blocked_url": sum(r["grade"]["metrics"]["blocked_url"] for r in rounds),
        "robots_denied": sum(r["grade"]["metrics"]["robots_denied"] for r in rounds),
        "dims": sorted({d for doc in docs for d in doc["dims"]}),
    }


def _write_report(run_dir: Path, summary: dict) -> Path:
    m = summary["metrics"]
    lines = [f"# 文本检索运行 {summary['run_id']}", "",
             f"- 时长 {summary['duration_ms']:.0f} ms；token 估算输入 "
             f"{summary['token_estimate']['input']} / 输出 {summary['token_estimate']['output']}",
             f"- 文章 {m['articles']} / 有 A 段 {m['articles_with_a']} / "
             f"A {m['a_chars']} 字（{m['a_share']*100:.1f}%）/ 单篇 {m['a_per_article']} 字",
             f"- 维度 {', '.join(m['dims']) or '无'} / 来源类型 {', '.join(m['source_types'])}",
             f"- 失败 {m['failed']}（blocked_url {m['blocked_url']} / robots {m['robots_denied']}）", ""]
    for r in summary.get("rounds", []):
        lines += [f"## 第 {r['round']} 轮 · {r['plan']['batch_id']}",
                  f"- 决策：{r['decision']['action']} — {'; '.join(r['decision']['reasons'])}",
                  f"- 计划来源：{r['plan'].get('profile_status')} / "
                  f"{', '.join(r['plan']['queries'].keys())}"]
        serp = r.get("serp", {})
        blocked_q = sum(1 for v in serp.values() if v.get("blocked"))
        if blocked_q:
            lines.append(f"- SERP 被拦 {blocked_q}/{len(serp)} 查询（百度验证/空结果）")
        for d in r["grade"]["docs"][:8]:
            lines.append(f"  - [{d['source_trust']}] {d['title'][:44]} · A {d['a_chars']} 字")
        lines.append("")
    path = run_dir / "report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run(intent_path: str | Path, data_dir: str | Path, *,
        registry_path: str | Path | None = None,
        profiles_path: str | Path | None = None,
        run_root: str | Path | None = None,
        run_id: str | None = None,
        do_replan: bool = True) -> dict:
    data_dir = Path(data_dir)
    intent = _load_json(intent_path)
    registry = load_registry(registry_path)
    profiles = load_profiles(profiles_path)
    category = intent.get("category")
    profile_name, profile = resolve_profile(category, profiles)
    ambiguous = ambiguity_unresolved(intent, category, profiles)

    log = runlog.RunLog(Path(run_root) if run_root else data_dir,
                        run_id=run_id,
                        meta={"intent": str(intent_path), "category": category,
                              "models": intent.get("models", []),
                              "profile": profile_name})
    log.llm(model="assistant-manual", prompt_version="text-plan-v0.1",
            input_text=json.dumps(intent, ensure_ascii=False),
            output_text=json.dumps({"profile": profile_name,
                                    "ambiguity": ambiguous}, ensure_ascii=False),
            note="确定性模板+档案生成计划；未接 LLM API，token 为估算")
    with log.stage("validate_intent"):
        validate(intent, "intent.schema.json")

    if ambiguous:
        dec = strategy.assess({}, profile_status="found" if profile else "missing",
                              ambiguity_unresolved=True)
        d = dec.as_dict()
        action, reasons = d.pop("action"), d.pop("reasons")
        log.decision(action, "; ".join(reasons), **d)
        out = log.finish(summary={"status": "need_clarification",
                                  "question": "意图存在歧义，请先确认类目/含义"},
                         metrics={})
        return out

    rounds = []
    max_rounds = int(intent.get("budget", {}).get("max_rounds", 2))
    for rno in range(1, max_rounds + 1):
        use_profile = profile if rno == 1 else None
        pname = profile_name if rno == 1 else None
        suffix = "" if rno == 1 else f"-r{rno}"
        with log.stage(f"plan_r{rno}", profile=profile_name,
                       profile_status="found" if use_profile else "missing"):
            plan = build_plan(intent, profile_name=pname, profile=use_profile,
                              registry=registry, round_no=rno, suffix=suffix,
                              wide=(rno > 1))
        (log.dir / f"plan-r{rno}.json").write_text(
            json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
        with log.stage(f"execute_r{rno}", batch_id=plan["batch_id"]):
            t0 = time.perf_counter()
            rep = corpus.collect_corpus(plan, data_dir)
            log.tool("corpus.collect_corpus",
                     args={"batch_id": plan["batch_id"],
                           "queries": len(plan["queries"]),
                           "quota": plan["quota"]},
                     result={"saved": rep["summary"].get("total", 0),
                             "serp_blocked": sum(
                                 1 for v in rep.get("serp", {}).values()
                                 if v.get("blocked"))},
                     duration_ms=(time.perf_counter() - t0) * 1000)
        with log.stage(f"grade_r{rno}", batch_id=plan["batch_id"]):
            grade = passage.grade_batch(Path(rep["outdir"]), registry)
        (log.dir / f"grade-r{rno}.json").write_text(
            json.dumps(grade, ensure_ascii=False, indent=1), encoding="utf-8")
        dec = strategy.assess(grade["metrics"],
                              profile_status=plan["profile_status"],
                              round_no=rno, max_rounds=max_rounds)
        d = dec.as_dict()
        action, reasons = d.pop("action"), d.pop("reasons")
        log.decision(action, "; ".join(reasons), round=rno, **d)
        rounds.append({"round": rno, "plan": plan, "grade": grade,
                       "serp": rep.get("serp", {}),
                       "decision": dec.as_dict()})
        if dec.action != "replan" or not do_replan:
            break

    metrics = _merge_metrics(rounds)
    summary = log.finish(summary={"status": "ok", "rounds": len(rounds),
                                  "final_action": rounds[-1]["decision"]["action"]},
                         metrics=metrics)
    summary["rounds"] = rounds
    report = _write_report(log.dir, summary)
    summary["artifacts"] = {"run_dir": str(log.dir), "report": str(report),
                            "events": str(log.events_path)}
    (log.dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary
