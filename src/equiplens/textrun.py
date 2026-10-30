"""文本检索编排器：intent → 类目档案 → 查询计划 → 执行 → 段落评估 → 低信度重规划。

原则:
- 控制流固定（workflow），内容判断在 L1/L3/L4 的关节上。
- 锁定项（robots/配额/账本/检查点/schema）不可被模型绕过。
- 每次运行写 runs/<run_id>/events.jsonl + summary.json（时间/token 估算/工具/决策）。
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import jsonschema

from . import audit, corpus, passage, runner, runlog, strategy

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
    query_meta: dict[str, dict] = {}
    aliases = list((profile or {}).get("aliases") or ([] if not category else [category]))
    comp_vocab = list((profile or {}).get("component_vocab") or [])
    design_words = ["造型", "设计语言", "家族化", "外观设计", "工业设计", "CMF",
                    "设计风格"]

    def _terms(info_type: str, extra: list[str] | None = None) -> list[str]:
        """按查询的信息类型给 relevant_terms——车型查询用车型词，
        类目/定调查询用类目词+设计语汇（T18-roster：全局车型名过滤会误杀
        类目级查询，导致 G 档归零）。"""
        base = {
            "vehicle": [*models, category or "", *aliases[:2]],
            "component": [category or "", *comp_vocab, *aliases[:2]],
            "macro": [*aliases[:2], category or "", *design_words],
        }[info_type]
        return list(dict.fromkeys([*(extra or []), *base, *design_words]))

    def add(q: str, st: str = "industry", info_type: str = "macro",
            extra_terms: list[str] | None = None) -> None:
        q = q.strip()
        if not q:
            return
        bucket = queries.setdefault(st, [])
        if q not in bucket:
            bucket.append(q)
        query_meta.setdefault(q, {"info_type": info_type,
                                  "relevant_terms": _terms(info_type, extra_terms)})

    # 1) 档案层：有档案时优先具体查询（预算截断时先保住类目相关）
    if profile:
        for alias in (profile.get("aliases") or [])[:2]:
            add(f"{alias} 造型 设计 语言", "industry", "macro")
        for model in models:
            add(f"{model} 外观 造型 设计 解读", "review", "vehicle",
                extra_terms=[model, *re.findall(r"[A-Za-z0-9\-]{2,}", model)])
        for comp in (profile.get("component_vocab") or [])[:4]:
            add(f"{category} {comp} 设计", "review", "component")
        for term in (profile.get("market_terms") or [])[:2]:
            add(f"{term} 造型 设计 趋势", "industry", "macro",
                extra_terms=[term])
    # 1b) 信源定向：优先域站内查询（域名来自数据文件 registry.preferred_domains）
    for domain in (registry.get("preferred_domains") or [])[:2]:
        if category:
            add(f"site:{domain} {category} 造型 设计", "review", "macro")
    # 2) 通用层/宽搜轮：宽搜轮只跑“不同的”查询，避免重复上一轮
    if wide:
        for q in ["工程机械 工业设计", "特种车辆 外观 设计 解读",
                  "商用车 CMF 色彩 材质 趋势", "作业车 造型 设计"]:
            add(q, "industry", "macro")
        if category:
            add(f"{category} 驾驶室 设计", "review", "component")
            add(f"{category} 工业设计 研究", "academic", "macro")
        add("专用车 造型 设计", "review", "macro")
        add("工程机械 造型设计 研究", "academic", "macro")
    else:
        for i, q in enumerate(strategy.generic_queries(category, models)):
            st = "industry" if i % 2 == 0 else "review"
            hit = next((m for m in models if m and m in q), None)
            if hit:  # 通用层里的车型查询仍按 vehicle 给词
                add(q, st, "vehicle",
                    extra_terms=[hit, *re.findall(r"[A-Za-z0-9\-]{2,}", hit)])
            else:
                add(q, st, "macro")

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

    kept_meta = {q: m for q, m in query_meta.items()
                 if any(q in qs for qs in queries.values())}
    plan = {
        "batch_id": f"batch-text-{time.strftime('%Y%m%d-%H%M%S')}{suffix}",
        "purpose": intent.get("task_type", "text_design_scan"),
        "category": category,
        "models": models,
        "profile_ref": profile_name,
        "profile_status": (profile.get("status") or "found") if profile else "missing",
        "queries": queries,
        "query_meta": kept_meta,
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
            res = runner.run_unit(
                runner.Unit(unit_id=f"{log.run_id}-r{rno}", plan=plan),
                collect=lambda p: corpus.collect_corpus(p, data_dir),
                grade=lambda outdir: passage.grade_batch(Path(outdir), registry),
                data_dir=data_dir, state_root=log.dir / "units")
            log.tool("runner.run_unit",
                     args={"unit": f"{log.run_id}-r{rno}",
                           "queries": len(plan["queries"]),
                           "quota": plan["quota"]},
                     result={"status": res.status, "attempts": res.attempts,
                             "channel": res.channel, "saved": res.saved,
                             "blockers": res.blockers},
                     duration_ms=(time.perf_counter() - t0) * 1000)
            rep = res.report
        if rep is None:  # 所有通道都失败：结构化上报后停止
            grade = {"docs": [], "metrics": {
                "articles": 0, "articles_with_a": 0, "total_chars": 0,
                "a_chars": 0, "b_chars": 0, "a_share": 0.0, "a_per_article": 0.0,
                "source_types": [], "failed": 0, "hard_failed": 0,
                "policy_skipped": 0, "blocked_url": 0, "robots_denied": 0,
                "dims": []}}
            log.decision("stop", "; ".join(res.blockers) or "all channels failed",
                         round=rno)
            rounds.append({"round": rno, "plan": plan, "grade": grade, "serp": {},
                           "decision": {"action": "stop",
                                        "reasons": res.blockers}})
            break
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
    # 每次运行自动生成误杀抽检包（5 分钟人工复核用），避免事后补做
    audit_info = None
    if rounds:
        bdir = data_dir / "corpus" / rounds[-1]["plan"]["batch_id"]
        if (bdir / "index.json").exists():
            rows = audit.collect_c_passages(bdir, registry)
            sheet = audit.build_sheet(rows, sample_per_stratum=2)
            (log.dir / "audit-sheet.json").write_text(
                json.dumps(sheet, ensure_ascii=False, indent=1), encoding="utf-8")
            (log.dir / "audit-sheet.md").write_text(
                audit.render_sheet_md(sheet), encoding="utf-8")
            audit_info = {"population": sheet["population"],
                          "guard": sheet["guard_count"],
                          "sample": sum(len(s["samples"])
                                        for s in sheet["strata"])}
    summary = log.finish(summary={"status": "ok", "rounds": len(rounds),
                                  "final_action": rounds[-1]["decision"]["action"],
                                  "audit": audit_info},
                         metrics=metrics)
    summary["rounds"] = rounds
    report = _write_report(log.dir, summary)
    summary["artifacts"] = {"run_dir": str(log.dir), "report": str(report),
                            "events": str(log.events_path)}
    (log.dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary
