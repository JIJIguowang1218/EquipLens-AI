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


def auto_limits(slots, backup: int = 4, n_queries: int = 1,
                per_query: int = 0, limit: int = 0) -> dict:
    """把“用户输入台数”换算成 planner 的目标池/每条查询抽取数/总上限。

    - need = 1.6 × (slots + backup)：候选池目标（由用户输入决定，不是固定值）；
    - per_query：按查询条数反推，保证总产出够 need（用户显式给了就用用户的）；
    - limit：候选截断上限，默认 = need。
    """
    need = pool_requirement(slots, backup)
    n = max(1, int(n_queries or 1))
    per = int(per_query) if int(per_query or 0) > 0 else max(
        8, int(math.ceil(need / n)) + 2)
    # 上限只用来防止无限膨胀；不要卡在 need 上——多出来的候选是备选补抓的余量，
    # 且提取已经发生，保留它们不额外花钱。12 台时保持原来的 36 不变。
    lim = int(limit) if int(limit or 0) > 0 else max(36, need)
    return {"need": need, "per_query": per, "limit": lim}


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


_PAREN_RE = re.compile(r"[（(][^）)]*[）)]")
# 泛称里不构成“身份”的词：构型/工况/车身/通用描述
_GENERIC_WORDS = ("沙漠", "全驱", "六驱", "四驱", "越野", "油田", "运输", "牵引",
                  "卡车", "货车", "专用", "特种", "改装", "可", "车", "头",
                  "马力", "吨级", "驾驶室", "底盘", "系列")


def strip_parens(text: str) -> str:
    return re.sub(r"\s+", "", _PAREN_RE.sub("", text or ""))


def has_qualifier(text: str) -> bool:
    """括号里的补充说明（如“可改装油田专用车”）算有效限定，不建议丢弃。"""
    return bool(_PAREN_RE.search(text or ""))


def generic_is_weak(model: str) -> bool:
    """泛称是否“弱到无法定位”：去掉括号/构型/通用词后没有型号、数字、品牌、车系。

    括号里的限定（如“可改装油田专用车”“460 马力”）算有效信息，不判弱。
    """
    if has_qualifier(model):
        return False
    t = strip_parens(model).lower().replace("×", "x")
    for w in _GENERIC_WORDS:
        t = t.replace(w, "")
    t = re.sub(r"\d+x\d+|\dx\d", "", t)
    return not re.search(r"[a-z]{2,}|\d{2,}", t)


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
    if len(set(clean)) >= 2:
        # 一条候选里出现两个不同型号码（如 HF 8066（H6066））→ 必须拆开，不能并
        return ("multi", tuple(sorted(set(clean))))
    if clean:
        code = sorted(set(clean), key=lambda c: (-len(c), c))[0]
        return ("code", code)
    series = next((x for x in SERIES if x in s), "")
    nums = re.findall(r"\b\d{3,}\b", s)
    if series and nums:
        return ("series", series, nums[0])
    if series:
        return ("series", series)
    core = strip_parens(s).replace("牵引车头", "牵引头")
    return ("generic", re.sub(r"[^0-9A-Z一-鿿]+", "", core))


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


def short_text(value, limit: int = 20) -> str:
    """把 brief 里的长描述压成适合搜索 query 的短词。

    2026-11-12 实测：LLM 生成的 environment.value / scope 是整段工况描述，
    直接拼进 query 会让 360 返回 0 结果或抽取为 0（正面吊/拖拉机/叉车）。
    规则：去括号补充、取第一个短句、限长。
    """
    t = normalize_text(value)
    if not t:
        return ""
    t = re.sub(r"[（(][^）)]*[）)]", " ", t)
    t = re.split(r"[，。；;、,]", t)[0]
    t = normalize_text(t)
    return t[:limit].strip()


def top_up_queries(brief: dict, existing: list[str] | None = None,
                   max_extra: int = 2) -> list[dict]:
    """候选池不足时追加的查询（默认最多 2 条）。

    只做"同义补充"，不换源、不加品牌白名单；查询同样要走
    validate_extraction（候选必须出自该查询的结果）。
    """
    req = brief.get("request") or {}
    klass = short_text(req.get("class"), 18)
    conf = short_text(req.get("configuration"), 10)
    if not klass:
        return []
    existing_norm = {normalize_text(x) for x in (existing or [])}
    pool = [f"{klass} {conf} 实车", f"{klass} {conf} 厂家"]
    out: list[dict] = []
    for q in pool:
        q = normalize_text(q)
        if not q or q in existing_norm:
            continue
        out.append({"query_id": f"q-topup-{len(out) + 1}", "dimension": "topup",
                    "query": q, "purpose": "候选池不足，补 1 条同义查询"})
        if len(out) >= max_extra:
            break
    return out


def negative_terms(brief: dict) -> list[str]:
    """只取适合放进搜索 query 的**短排除词**；句子/指令会毁掉查询。

    2026-11-12 复现：新 brief 的 negative 里混进了
    「不引入具体品牌/型号或“同系列”作为设计理由。」这类指令（23 字，旧过滤器放过），
    被拼进每条 query 后，沙漠牵引车候选从 22 掉到 11。
    """
    banned = ("不", "勿", "禁止", "避免", "必须", "请", "作为", "理由", "分析",
              "取证", "输出", "字段", "配额", "预算", "单元", "用户", "点名",
              "仅", "除非", "标注", "拆", "扩展", "补充", "跨")
    meta = {"模型", "品牌", "型号", "车型", "汽车", "卡车", "车", "图片", "素材"}
    out: list[str] = []
    for x in (brief.get("negative") or [])[:8]:
        t = normalize_text(x).strip("“”\"'")
        if not t or len(t) > 8:
            continue
        if any(b in t for b in banned):
            continue
        if t in meta:
            continue
        if re.search(r"[，。；、,;:/]", t):
            continue
        if t not in out:
            out.append(t)
    return out[:4]


def build_query_plan(brief: dict, extra: list[str] | None = None, *,
                     use_negative: bool = True) -> list[dict]:
    """任务单 → 查询计划（每条带 query_id / dimension / purpose）。

    `extra` 只用于覆盖实验，必须是“市场段/工况”描述，不允许写品牌名单。

    `use_negative=False` 只用于 A/B：查询文本与默认路径**逐字相同**，只是
    不追加 `-"短词"` 后缀；brief 本身不改（仍是同一份任务单）。
    """
    req = brief.get("request") or {}
    # 只取短词：长描述直接拼 query 会让搜索 0 结果（2026-11-12 交付测试复现）
    env = short_text((req.get("environment") or {}).get("value"), 14)
    klass = short_text(req.get("class"), 18)
    conf = short_text(req.get("configuration"), 10)
    neg = (" ".join(f'-"{x}"' for x in negative_terms(brief))
           if use_negative else "")

    rows: list[dict] = []

    def add(dimension: str, query_id: str, query: str, purpose: str) -> None:
        q = normalize_text(query)
        if q:
            rows.append({"query_id": query_id, "dimension": dimension,
                         "query": q, "purpose": purpose})

    # 关键：短 ≠ 相同。每类查询要有不同的“检索意图”，否则 360 返回同一批结果，
    # 去重后候选会塌缩（2026-11-12 实测：查询高度重合时 30 条抽取只剩 9 台车）。
    add("base", "q-base", short_text(" ".join(x for x in (env, klass, conf) if x), 34),
        "工况 + 类目 + 构型")
    add("model", "q-model", short_text(f"{klass} {conf} 车型 品牌", 30),
        "车型候选主查询")
    add("environment", "q-env", short_text(f"{env} {conf} 卡车 车型", 30),
        "邻域工况/上装")
    add("english", "q-en", short_text(f"{klass} {conf} truck brands", 30),
        "英文品牌兜底")

    for unit in brief.get("research_units") or []:
        uid = normalize_text(unit.get("unit_id")) or f"u{len(rows)}"
        scope = short_text(unit.get("scope"), 20)
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

    规则（2026-11-12 人审后补充）：
    - 同码（TAZ4922 / DFV5253TSMGP6D）→ 合并，保留所有写法到 `model_variants`；
    - 一条记录里出现**两个不同型号码**（如 `HF 8066（H6066）`）→ 拆成两条，不并；
    - 泛称：去掉括号补充后再比较，`6×6全驱沙漠车` 与
      `6×6 全驱沙漠车（可改装油田专用车）` 视为同款（保留信息更全的那条）；
    - 泛称且去掉通用词后没有任何型号/数字/品牌/限定 → 丢弃（如 `6×6沙漠卡车`）；
    - Zetros 4051 与 Zetros 3643 → 不同身份，保留两台。
    """
    merged: dict[tuple, dict] = {}
    order: list[tuple] = []

    def _same_generic(ident: tuple) -> tuple:
        """泛称近似合并：差一个品牌前缀（如“东风 …” vs “…”，≤4 个中文字）算同款。"""
        if ident[0] != "generic":
            return ident
        k1 = ident[1]
        for k2 in order:
            if merged[k2].get("identity_kind") != "generic":
                continue
            s2 = k2[1]
            a, b = (k1, s2) if len(k1) >= len(s2) else (s2, k1)
            if not a.endswith(b):
                continue
            diff = a[: len(a) - len(b)]
            if diff and len(diff) <= 4 and re.fullmatch(r"[一-鿿]+", diff):
                return k2
        return ident

    def _absorb(ident: tuple, item: dict) -> None:
        ident = _same_generic(ident)
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
            return
        cur = merged[ident]
        for u in item.get("sources") or []:
            if u not in cur["sources"]:
                cur["sources"].append(u)
        q = {"query_id": item.get("source_query_id"),
             "query": item.get("source_query")}
        if q not in cur["source_queries"]:
            cur["source_queries"].append(q)
        if item.get("dimension") not in cur["dimensions"]:
            cur["dimensions"].append(item.get("dimension"))
        if item.get("model") not in cur["model_variants"]:
            cur["model_variants"].append(item.get("model"))
        cur["source_count"] = len(cur["sources"])

    for item in items:
        ident = model_identity(item.get("model"))
        if ident[0] == "multi":
            # 多码记录：一条拆成两条，各自走身份合并（H6066 归 H6066，8066 独立）
            for code in ident[1]:
                _absorb(("code", code), item)
            continue
        _absorb(ident, item)

    out: list[dict] = []
    for k in order:
        c = merged[k]
        if c.get("identity_kind") == "generic":
            variants = c.get("model_variants") or [c.get("model")]
            if all(generic_is_weak(v) for v in variants):
                continue      # 弱泛称：无型号/数字/品牌/限定，人审判定不该保留
        out.append(c)
    return out


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
