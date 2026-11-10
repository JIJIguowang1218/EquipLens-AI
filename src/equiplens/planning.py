# -*- coding: utf-8 -*-
"""候选规划的可测试核心（不联网、不调 LLM）。

把“查询怎么来、候选怎么归并、来源怎么校验、覆盖怎么报”从脚本里拆出来，
让 planner 从“一次性大 prompt”变成可解释的流水线：

  brief → build_query_plan（每条查询带 query_id/dimension/purpose）
        → 每条查询单独检索、单独抽取（候选必须带 sources）
        → validate_extraction（URL 必须属于该查询）
        → merge_candidates（同车型合并，保留来源查询）
        → coverage_report（哪个维度有货、哪个维度空）
"""
from __future__ import annotations

import re

# 覆盖维度：查询只描述“工况/类目/构型/市场段”，不写品牌名单
CORE_DIMENSIONS = ("base", "model", "environment")
INTERNATIONAL_HINTS = ("进口", "国际品牌", "海外", "欧美", "俄系")


def normalize_text(value) -> str:
    return " ".join(str(value or "").split())


def candidate_key(model: str) -> str:
    """车型名的去重键：大小写/空格/标点/× 归一，中文保留。"""
    s = normalize_text(model).lower().replace("×", "x")
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", s)


def _with_conf(scope: str, conf: str) -> str:
    scope = normalize_text(scope)
    conf = normalize_text(conf)
    if not conf:
        return scope
    if conf.lower().replace("×", "x") in scope.lower().replace("×", "x"):
        return scope
    return f"{scope} {conf}".strip()


def negative_terms(brief: dict) -> list[str]:
    return [normalize_text(x) for x in (brief.get("negative") or [])[:4] if normalize_text(x)]


def build_query_plan(brief: dict, extra: list[str] | None = None) -> list[dict]:
    """任务单 → 查询计划（每条带 query_id / dimension / purpose）。

    `extra` 只用于覆盖实验，必须是“市场段/工况”描述，不允许写品牌名单。
    """
    req = brief.get("request") or {}
    env = normalize_text((req.get("environment") or {}).get("value"))
    klass = normalize_text(req.get("class"))
    conf = normalize_text(req.get("configuration"))
    neg = " ".join(f'-"{x}"' for x in negative_terms(brief))

    rows: list[dict] = []

    def add(dimension: str, query_id: str, query: str, purpose: str) -> None:
        q = normalize_text(query)
        if q:
            rows.append({"query_id": query_id, "dimension": dimension,
                         "query": q, "purpose": purpose})

    add("base", "q-base", " ".join(x for x in (env, klass, conf) if x),
        "工况 + 类目 + 构型")
    add("model", "q-model", f"{klass} {conf} 车型 品牌", "车型候选主查询")
    add("environment", "q-env", f"{env} {conf} 卡车 车型", "邻域工况/上装")
    add("english", "q-en", f"{klass} {conf} truck brands", "英文品牌兜底")

    for unit in brief.get("research_units") or []:
        uid = normalize_text(unit.get("unit_id")) or f"u{len(rows)}"
        scope = normalize_text(unit.get("scope"))
        add("unit", f"q-unit-{uid}", _with_conf(scope, conf),
            f"research_unit {uid} 的 scope")
    for i, q in enumerate(extra or [], start=1):
        add("extra", f"q-extra-{i}", q, "覆盖实验查询")

    # 同一查询只保留第一次出现（查询顺序 = 优先级）
    seen: set[str] = set()
    plan: list[dict] = []
    for row in rows:
        if row["query"] in seen:
            continue
        seen.add(row["query"])
        row["query"] = row["query"] + (" " + neg if neg else "")
        plan.append(row)
    return plan


def validate_extraction(payload: dict, allowed_urls: set[str], query_meta: dict,
                        limit: int = 6) -> tuple[list[dict], dict]:
    """校验 LLM 从**单条查询**抽出的候选。

    - 每条候选必须至少 1 个 URL 属于这条查询自己的结果；
    - 不在结果集里的 URL 直接剔除（不信任模型给的链接）；
    - 记录丢弃原因，供 coverage 报告解释“为什么这条查询没产出”。
    """
    rows: list[dict] = []
    dropped_no_source = 0
    dropped_invalid = 0
    seen: set[str] = set()
    for cand in (payload or {}).get("candidates") or []:
        model = normalize_text(cand.get("model"))
        if not model:
            continue
        key = candidate_key(model)
        if not key or key in seen:
            continue
        srcs = [normalize_text(u) for u in (cand.get("sources") or [])]
        valid = [u for u in srcs if u in allowed_urls]
        dropped_invalid += max(0, len(srcs) - len(valid))
        if not valid:
            dropped_no_source += 1
            continue
        seen.add(key)
        rows.append({
            "model": model,
            "brand": normalize_text(cand.get("brand")),
            "reason": normalize_text(cand.get("reason"))[:200],
            "sources": valid,
            "source_query": query_meta["query"],
            "source_query_id": query_meta["query_id"],
            "dimension": query_meta["dimension"],
        })
        if len(rows) >= limit:
            break
    stats = {"kept": len(rows), "dropped_no_source": dropped_no_source,
             "dropped_invalid_source": dropped_invalid}
    return rows, stats


def merge_candidates(items: list[dict]) -> list[dict]:
    """同一车型跨查询合并：来源取并集，保留第一次出现的排序位置。"""
    merged: dict[str, dict] = {}
    order: list[str] = []
    for item in items:
        key = candidate_key(item.get("model"))
        if not key:
            continue
        if key not in merged:
            merged[key] = dict(item)
            merged[key]["source_queries"] = [
                {"query_id": item.get("source_query_id"),
                 "query": item.get("source_query")}
            ]
            merged[key]["dimensions"] = [item.get("dimension")]
            merged[key]["source_count"] = len(item.get("sources") or [])
            order.append(key)
            continue
        cur = merged[key]
        for u in item.get("sources") or []:
            if u not in cur["sources"]:
                cur["sources"].append(u)
        q = {"query_id": item.get("source_query_id"), "query": item.get("source_query")}
        if q not in cur["source_queries"]:
            cur["source_queries"].append(q)
        if item.get("dimension") not in cur["dimensions"]:
            cur["dimensions"].append(item.get("dimension"))
        cur["source_count"] = len(cur["sources"])
    return [merged[k] for k in order]


def coverage_report(plan: list[dict], candidates: list[dict]) -> dict:
    dims: dict[str, dict] = {}
    for row in plan:
        d = dims.setdefault(row["dimension"], {"queries": 0, "candidates": 0})
        d["queries"] += 1
    for cand in candidates:
        for dim in cand.get("dimensions") or []:
            if dim in dims:
                dims[dim]["candidates"] += 1
    has_intl = any(any(h in (c.get("source_query") or "") for h in INTERNATIONAL_HINTS)
                   for c in candidates) or any(
        any(h in (q.get("query") or "") for h in INTERNATIONAL_HINTS) for q in plan)
    return {
        "dimensions": dims,
        "missing": [d for d in CORE_DIMENSIONS
                    if dims.get(d, {}).get("candidates", 0) == 0],
        "international_covered": bool(has_intl),
        "queries": len(plan),
        "candidates": len(candidates),
    }
