# -*- coding: utf-8 -*-
"""TaskSpec normalization / validation (S0-01, v0.4).

LLM 只负责“从输入里抽字段”；本模块负责**确定性的规范化与校验**：
- 固定枚举：`policy.hard/soft` 只允许 schema 字段名；
- 软字段不得进 hard（views/quality/…）；非法自由词降级到 `unknowns`；
- modify 语义：`quantity.delta`，`primary` 置空；
- 品牌配额、foreign_ratio、origin/powertrain 的数值/枚举归一；
- parts 与 constraints.exclude 去重；
- 提问策略：最多 1 条，且必须存在 blocking 未知项。

不含任何领域实体枚举（品牌/车型/类目别名词表）；别名归一必须由调用方通过
`alias_map` 显式传入（见 docs/vocabulary-policy.md §5）。
"""
from __future__ import annotations

import copy
import re

HARD_FIELDS = (
    "quantity", "class", "brands_include", "brands_exclude", "models_pinned",
    "constraints.exclude", "constraints.origin", "constraints.powertrain",
    "configuration", "environment",
)
SOFT_FIELDS = (
    "views", "quality", "year", "tonnage", "price", "soft_brands",
    "foreign_ratio", "brand_quota",
)
SOFT_ONLY = frozenset(SOFT_FIELDS)
SEVERITIES = ("blocking", "defaultable", "informational")
POWERTRAIN = {"电动": "electric", "纯电": "electric", "electric": "electric",
              "柴油": "diesel", "diesel": "diesel", "混动": "hybrid", "hybrid": "hybrid"}
ORIGIN = {"国产": "domestic", "domestic": "domestic", "进口": "import", "import": "import"}


def _norm(s) -> str:
    return re.sub(r"[\s\-_（）()×xX·]", "", str(s or "")).lower()


def _as_int(v):
    if isinstance(v, bool) or v is None:
        return None
    try:
        n = int(v)
    except (TypeError, ValueError):
        return None
    return n if n >= 0 else None


def _dedupe(items):
    out, seen = [], set()
    for x in items or []:
        k = str(x).strip()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _freeform_to_field(value: str):
    """把模型偶发的自由词映射到 schema 字段；只做结构映射，不查实体表。"""
    v = str(value or "").strip().lower()
    if v in ("domestic_only", "domestic"):
        return "constraints.origin"
    if v in ("import_only", "import"):
        return "constraints.origin"
    if v in ("electric_only", "electric"):
        return "constraints.powertrain"
    if v in ("quantity_backup",):
        return "quantity"
    if v in ("views", "quality", "year", "tonnage", "price", "soft_brands",
             "foreign_ratio", "brand_quota"):
        return v
    if v in ("constraints_exclude", "exclude"):
        return "constraints.exclude"
    return None


def normalize(spec: dict, *, alias_map: dict | None = None) -> dict:
    """返回规范化后的副本；不修改入参。"""
    s = copy.deepcopy(spec or {})

    # 类目：只做“显式传入的别名映射”，默认不查表
    cls = s.get("class")
    raw = s.get("class_raw") or cls
    aliases = _dedupe(s.get("class_aliases") or [])
    if alias_map and cls and cls in alias_map:
        mapped = alias_map[cls]
        if mapped and mapped != cls:
            aliases = _dedupe(aliases + [cls])
            cls = mapped
    s["class"] = cls or None
    s["class_raw"] = raw or cls or None
    s["class_aliases"] = aliases

    if isinstance(s.get("configuration"), str):
        s["configuration"] = s["configuration"].replace("×", "x").replace(" ", "")

    q = s.setdefault("quantity", {})
    if not isinstance(q, dict):
        q = s["quantity"] = {}
    for k in ("primary", "backup", "delta"):
        q[k] = _as_int(q.get(k))
    if s.get("intent") == "modify" and q.get("primary") and not q.get("delta"):
        q["delta"] = q.pop("primary")
        q["primary"] = None
    if q.get("backup") is not None and q.get("delta") is not None:
        # 两者不互斥，但同一字段来源常混；保留两者，交给业务判断
        pass

    prefs = s.setdefault("preferences", {})
    if not isinstance(prefs, dict):
        prefs = s["preferences"] = {}
    prefs["soft_brands"] = _dedupe(prefs.get("soft_brands"))
    views = {str(v).lower() for v in prefs.get("views") or []}
    prefs["views"] = [v for v in ("front", "45", "side", "rear", "roof") if v in views]
    prefs["quality"] = _dedupe(prefs.get("quality"))
    fr = prefs.get("foreign_ratio")
    if isinstance(fr, dict):
        lo, hi = fr.get("min"), fr.get("max")
        try:
            lo = float(lo) if lo is not None else None
            hi = float(hi) if hi is not None else None
        except (TypeError, ValueError):
            lo = hi = None
        prefs["foreign_ratio"] = {"min": lo, "max": hi} if (lo is not None or hi is not None) else None
    else:
        prefs["foreign_ratio"] = None

    quota = prefs.get("brand_quota")
    if isinstance(quota, dict):
        brands = _dedupe(quota.get("brands"))
        mn, of = _as_int(quota.get("min")), _as_int(quota.get("of"))
        if brands and mn and of and mn <= of:
            prefs["brand_quota"] = {"brands": brands, "min": mn, "of": of}
        else:
            prefs["brand_quota"] = None
            s.setdefault("unknowns", []).append(
                {"field": "brand_quota", "text": "品牌配额缺品牌/台数或 min>of，无法落库",
                 "severity": "informational", "proposal": ""})
    else:
        prefs["brand_quota"] = None

    cons = s.setdefault("constraints", {})
    if not isinstance(cons, dict):
        cons = s["constraints"] = {}
    cons["exclude"] = _dedupe(cons.get("exclude"))
    for k, mp in (("origin", ORIGIN), ("powertrain", POWERTRAIN)):
        v = cons.get(k)
        if v is None or v == "":
            cons[k] = None
        else:
            cons[k] = mp.get(str(v).strip(), str(v).strip())

    prov = []
    for m in s.get("models_provided") or []:
        if isinstance(m, dict) and str(m.get("model") or "").strip():
            prov.append({"model": str(m["model"]).strip(), "image": bool(m.get("image", True))})
    s["models_provided"] = prov

    # parts 与 exclude 去重（同一词不两边都留）
    ex = {_norm(x) for x in cons.get("exclude") or []}
    s["parts"] = [p for p in _dedupe(s.get("parts")) if _norm(p) not in ex]

    # policy：固定枚举 + 软字段不得进 hard
    pol = s.setdefault("policy", {})
    if not isinstance(pol, dict):
        pol = s["policy"] = {}
    hard = _dedupe(pol.get("hard"))
    soft = _dedupe(pol.get("soft"))
    bad = []
    new_hard, new_soft = [], list(soft)
    for v in hard:
        if v in HARD_FIELDS:
            new_hard.append(v)
        elif v in SOFT_ONLY:
            new_soft.append(v)
        else:
            mapped = _freeform_to_field(v)
            if mapped in HARD_FIELDS:
                new_hard.append(mapped)
                if mapped == "constraints.origin" and not cons.get("origin"):
                    cons["origin"] = "domestic"
                if mapped == "constraints.powertrain" and not cons.get("powertrain"):
                    cons["powertrain"] = "electric"
            elif mapped in SOFT_ONLY:
                new_soft.append(mapped)
            else:
                bad.append(v)
    for v in soft:
        if v not in HARD_FIELDS and v not in SOFT_ONLY:
            mapped = _freeform_to_field(v)
            if mapped:
                new_soft.append(mapped)
            else:
                bad.append(v)
    pol["hard"] = _dedupe(new_hard)
    pol["soft"] = [v for v in _dedupe(new_soft) if v not in pol["hard"]]
    for v in _dedupe(bad):
        s.setdefault("unknowns", []).append(
            {"field": v, "text": f"未支持的策略字段 {v}，已降级", "severity": "informational", "proposal": ""})

    # 未知项分级 + 提问策略
    unk = []
    for u in s.get("unknowns") or []:
        if not isinstance(u, dict):
            continue
        sev = u.get("severity") if u.get("severity") in SEVERITIES else "informational"
        unk.append({"field": str(u.get("field") or ""), "text": str(u.get("text") or ""),
                    "severity": sev, "proposal": str(u.get("proposal") or "")})
    s["unknowns"] = unk
    blocking = [u for u in unk if u["severity"] == "blocking"]
    qs = [q for q in (s.get("questions") or []) if isinstance(q, dict)]
    s["questions"] = qs[:1] if blocking else []

    sc = s.get("scope")
    if isinstance(sc, dict):
        adj = _as_int(sc.get("adjacent"))
        s["scope"] = {"mode": sc.get("mode") or "mixed", "adjacent": adj} if adj else None
    else:
        s["scope"] = None
    return s


def validate(spec: dict) -> list[str]:
    """结构性校验；返回问题列表（空 = 通过）。"""
    issues: list[str] = []
    if not isinstance(spec, dict):
        return ["spec 不是对象"]
    if spec.get("intent") not in ("new_task", "modify", "question"):
        issues.append("intent 非法")
    q = spec.get("quantity") or {}
    for k in ("primary", "backup", "delta"):
        if q.get(k) is not None and (not isinstance(q[k], int) or q[k] < 0):
            issues.append(f"quantity.{k} 非法")
    quota = (spec.get("preferences") or {}).get("brand_quota")
    if quota and quota.get("min", 0) > quota.get("of", 0):
        issues.append("brand_quota min>of")
    for bucket in ("hard", "soft"):
        for v in (spec.get("policy") or {}).get(bucket) or []:
            if v not in HARD_FIELDS and v not in SOFT_FIELDS:
                issues.append(f"policy.{bucket} 非法字段 {v}")
    if len(spec.get("questions") or []) > 1:
        issues.append("questions > 1")
    for u in spec.get("unknowns") or []:
        if u.get("severity") not in SEVERITIES:
            issues.append(f"severity 非法 {u.get('severity')}")
    sc = spec.get("scope") or {}
    if sc.get("adjacent") is not None and (not isinstance(sc["adjacent"], int) or sc["adjacent"] < 0):
        issues.append("scope.adjacent 非法")
    return issues


def to_brief(spec: dict) -> dict:
    """把 TaskSpec 映射成 brief 的**部分** request（由调用方合并，不覆盖其它字段）。"""
    s = normalize(spec)
    q = s.get("quantity") or {}
    req = {
        "class": s.get("class") or "",
        "configuration": s.get("configuration") or "",
        "page_budget": {
            "vehicle_slots": q.get("primary"),
            "backup_slots": q.get("backup"),
        },
    }
    env = s.get("environment")
    if env:
        req["environment"] = {"value": env}
    pinned = []
    for m in s.get("models_pinned") or []:
        mm = m.get("model") if isinstance(m, dict) else m
        if mm:
            pinned.append(str(mm))
    cons = s.get("constraints") or {}
    req.update({
        "brands_include": [str(x) for x in (s.get("brands_include") or [])],
        "brands_exclude": [str(x) for x in (s.get("brands_exclude") or [])],
        "models_pinned": pinned,
        "constraints": {"exclude": [str(x) for x in (cons.get("exclude") or [])],
                        "views": [str(x) for x in (cons.get("views") or [])]},
    })
    return {"request": req, "taskspec": s}
