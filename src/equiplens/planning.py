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

import math
import re

# 覆盖维度：查询只描述“工况/类目/构型/市场段”，不写品牌名单
CORE_DIMENSIONS = ("base", "model", "environment")

# 候选池下限系数：交付 = slots + backup，且有图率约 75%，所以要 1.6 倍余量
POOL_FACTOR = 1.6


def pool_requirement(slots, backup: int = 4, factor: float = POOL_FACTOR) -> int:
    """主槽 + 备选所需的最少候选池（含无图余量）。

    依据（2026-11-12 实测）：发现 26 台时有图约 19 台（73%）；12 主 + 4 备
    需要 16 台有图，池子 < 26 就会在备选上 short。
    """
    try:
        slots = int(slots or 0)
        backup = int(backup or 0)
    except (TypeError, ValueError):
        return 0
    if slots <= 0:
        return 0
    return int(math.ceil(float(factor) * (slots + backup)))


def pool_warning(count, slots, backup: int = 4) -> str:
    """候选池不足时返回一句告警；够则返回空串。"""
    need = pool_requirement(slots, backup)
    if need and int(count or 0) < need:
        return (f"候选池 {count} < 建议 {need}（1.6×({slots}+{backup})）："
                f"按当前有图率可能凑不齐备选，建议扩池或接受 short")
    return ""
INTERNATIONAL_HINTS = ("进口", "国际品牌", "海外", "欧美", "俄系")


def normalize_text(value) -> str:
    return " ".join(str(value or "").split())


def candidate_key(model: str) -> str:
    """旧口径：整串归一（只用于无车型身份时的兜底，不再用于同款合并）。"""
    s = normalize_text(model).lower().replace("×", "x")
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", s)


# 车系（无型号码时用）；注意不要放品牌名，否则会把同品牌多台车并成一台
SERIES = ("ZETROS", "AROCS", "ACTROS", "X3000", "X5000", "M3000",
          "F3000", "HOWO")
_CODE_PATTERNS = (
    re.compile(r"\b[A-Z]{1,6}-?\d{3,}[A-Z0-9-]*\b"),   # TAZ4922 / K-65959 / DFV5253TSMGP6D
    re.compile(r"\b[A-Z]{2,3}\s\d{3,}\b"),              # TB 800
)
# 这些是参数单位/缩写，不是型号（K-65959（GVW 35000 kg）里的 GVW35000 是假型号码）
_CODE_STOPWORDS = {"GVW", "HP", "KW", "NM", "KG", "MM", "CM", "CC",
                   "RPM", "TON", "MPH", "KPH", "L", "T"}


def _identity_text(model: str) -> str:
    s = normalize_text(model).upper().replace("×", "X")
    s = re.sub(r"\d+(\.\d+)?\s*马力", " ", s)   # 460马力 不是型号
    s = re.sub(r"\d+(\.\d+)?\s*吨", " ", s)
    return s


def model_identity(model: str) -> tuple:
    """车型身份（用于合并同款，不用于品牌去重）。

    优先级：
      1) 型号码（TAZ4922 / DFV5253TSMGP6D / K-65959 / TB800）→ 同码合并；
      2) 车系 + 数字（Zetros 4051 / Zetros 3643）→ 同车系同数字合并；
      3) 只有车系（Arocs）→ 同车系合并；
      4) 都没有 → generic（保留，不与有型号码的车硬并）。
    """
    s = _identity_text(model)
    codes: list[str] = []
    for pat in _CODE_PATTERNS:
        codes += [re.sub(r"[^A-Z0-9]", "", m) for m in pat.findall(s)]
    clean: list[str] = []
    for code in codes:
        prefix = re.match(r"[A-Z]+", code)
        if prefix and prefix.group(0) in _CODE_STOPWORDS:
            continue
        if any(ch.isalpha() for ch in code) and any(ch.isdigit() for ch in code):
            clean.append(code)
    if clean:
        code = sorted(set(clean), key=lambda c: (-len(c), c))[0]
        return ("code", code)
    series = next((x for x in SERIES if x in s), "")
    nums = re.findall(r"\b\d{3,}\b", s)
    if series and nums:
        return ("series", series, nums[0])
    if series:
        return ("series", series)
    return ("generic", re.sub(r"[^0-9A-Z\u4e00-\u9fff]+", "", s))


def identity_label(identity: tuple) -> str:
    return "/".join(str(x) for x in identity)


def _with_conf(scope: str, conf: str) -> str:
    scope = normalize_text(scope)
    conf = normalize_text(conf)
    if not conf:
        return scope
    if conf.lower().replace("×", "x") in scope.lower().replace("×", "x"):
        return scope
    return f"{scope} {conf}".strip()


def negative_terms(brief: dict) -> list[str]:
    """只取适合放进搜索 query 的短负词；长句/指令不要拼进 query。

    2026-11-11：task-brief 的 negative 可能写成“不要把前脸拆成……”这类指令，
    直接拼进 360 query 会把所有查询变成 0 结果（新 brief 实测）。
    """
    out = []
    for x in (brief.get("negative") or [])[:4]:
        t = normalize_text(x)
        if not t or len(t) > 24:
            continue
        if any(m in t for m in ("不要", "不得", "禁止", "避免", "必须", "请")):
            continue
        out.append(t)
    return out


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
    """按**车型身份**合并同款变体；同品牌不同型号码不合并。

    - 同码（TAZ4922 / DFV5253TSMGP6D）→ 合并，保留所有写法到 `model_variants`；
    - Zetros 4051 与 Zetros 3643 → 不同身份，保留两台；
    - 东风 EQ2251AX / EQ2220AX → 不同身份，保留两台；
    - 没有型号码/车系的泛称 → generic，单独保留（不与具体车型硬并）。
    """
    merged: dict[tuple, dict] = {}
    order: list[tuple] = []
    for item in items:
        ident = model_identity(item.get("model"))
        if ident[0] == "generic" and not ident[1]:
            continue
        if ident not in merged:
            merged[ident] = dict(item)
            merged[ident]["identity"] = identity_label(ident)
            merged[ident]["identity_kind"] = ident[0]
            merged[ident]["model_variants"] = [item.get("model")]
            merged[ident]["source_queries"] = [
                {"query_id": item.get("source_query_id"),
                 "query": item.get("source_query")}
            ]
            merged[ident]["dimensions"] = [item.get("dimension")]
            merged[ident]["source_count"] = len(item.get("sources") or [])
            order.append(ident)
            continue
        cur = merged[ident]
        for u in item.get("sources") or []:
            if u not in cur["sources"]:
                cur["sources"].append(u)
        q = {"query_id": item.get("source_query_id"), "query": item.get("source_query")}
        if q not in cur["source_queries"]:
            cur["source_queries"].append(q)
        if item.get("dimension") not in cur["dimensions"]:
            cur["dimensions"].append(item.get("dimension"))
        if item.get("model") not in cur["model_variants"]:
            cur["model_variants"].append(item.get("model"))
        cur["source_count"] = len(cur["sources"])
    return [merged[k] for k in order]


def dedupe_stats(raw_items: list[dict], merged: list[dict]) -> dict:
    return {
        "input": len(raw_items),
        "unique": len(merged),
        "removed": max(0, len(raw_items) - len(merged)),
        "generic": sum(1 for c in merged if c.get("identity_kind") == "generic"),
    }


def coverage_report(plan: list[dict], candidates: list[dict],
                    slots: int | None = None) -> dict:
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
    report = {
        "dimensions": dims,
        "missing": [d for d in CORE_DIMENSIONS
                    if dims.get(d, {}).get("candidates", 0) == 0],
        "international_covered": bool(has_intl),
        "queries": len(plan),
        "candidates": len(candidates),
    }
    if slots:
        report["slots"] = int(slots)
        report["pool_shortfall"] = max(0, int(slots) - len(candidates))
    return report
