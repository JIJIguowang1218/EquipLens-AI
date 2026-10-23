"""低信度逃生口：何时允许模型“退一步重规划”，以及它能改什么、不能改什么。

这是 L4 的确定性基线。模型接入后可以在 scope 内自主选择具体动作；
但 scope 之外（合规/配额/账本/检查点）永远不可越过。
"""

from __future__ import annotations

from dataclasses import dataclass, field

LOCKED = [
    "robots/UA/授权",
    "配额上限",
    "账本不变量",
    "原图不可变",
    "人工检查点",
    "schema 校验",
]


@dataclass
class Decision:
    action: str  # ok | replan | ask_user | stop
    reasons: list[str]
    scope: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=lambda: list(LOCKED))

    def as_dict(self) -> dict:
        return {"action": self.action, "reasons": self.reasons,
                "scope": self.scope, "constraints": self.constraints}

    def __getitem__(self, key: str):
        return getattr(self, key)


DEFAULTS = {
    "min_articles": 3,
    "min_a_share": 0.06,
    "min_source_types": 2,
    "max_failure_rate": 0.6,
    "min_a_chars_for_ok": 300,
}


def assess(metrics: dict, *, profile_status: str = "found",
           ambiguity_unresolved: bool = False, round_no: int = 1,
           max_rounds: int = 2, thresholds: dict | None = None) -> Decision:
    """根据本轮指标给出：继续 / 重规划 / 问用户 / 停止。"""
    t = dict(DEFAULTS)
    t.update(thresholds or {})
    reasons: list[str] = []
    if ambiguity_unresolved:
        return Decision("ask_user", ["意图存在未确认歧义，先问用户"],
                        scope=["intent_clarification"])
    articles = int(metrics.get("articles", 0))
    a_share = float(metrics.get("a_share", 0.0))
    a_chars = int(metrics.get("a_chars", 0))
    source_types = metrics.get("source_types", []) or []
    failed = int(metrics.get("hard_failed", metrics.get("failed", 0)))
    saved = articles
    failure_rate = failed / (failed + saved) if (failed + saved) else 0.0
    budget_exhausted = round_no >= max_rounds
    if articles < t["min_articles"]:
        reasons.append(f"文章数 {articles} < {t['min_articles']}")
    if a_share < t["min_a_share"]:
        reasons.append(f"A 占比 {a_share:.1%} < {t['min_a_share']:.1%}")
    if a_chars < t["min_a_chars_for_ok"]:
        reasons.append(f"A 字数 {a_chars} < {t['min_a_chars_for_ok']}")
    if len(source_types) < t["min_source_types"]:
        reasons.append(f"来源类型 {len(source_types)} < {t['min_source_types']}")
    if failure_rate > t["max_failure_rate"]:
        reasons.append(f"失败率 {failure_rate:.0%} > {t['max_failure_rate']:.0%}")
    if profile_status == "missing" and (a_share < t["min_a_share"] or a_chars < 200):
        reasons.append("类目档案缺失且通用层产出不足")
    if not reasons:
        return Decision("ok", ["指标达标"], scope=[])
    if budget_exhausted:
        reasons.append(f"已用 {round_no}/{max_rounds} 轮，停止并上报缺口")
        return Decision("stop", reasons, scope=[])
    scope = ["expand_design_queries", "switch_sources"]
    if profile_status == "missing":
        scope += ["generic_layer", "propose_profile"]
    if ambiguity_unresolved:
        scope += ["ask_user"]
    return Decision("replan", reasons, scope=scope)


def generic_queries(category: str | None, models: list[str] | None = None) -> list[str]:
    """类目无关的通用设计查询；新类目缺档案时的兜底。"""
    q = [
        "工程机械 造型 设计",
        "商用车 设计 语言 家族化",
        "工程车辆 外观 设计 解读",
        "驾驶室 造型 设计",
    ]
    if category:
        q += [f"{category} 造型 设计 解读", f"{category} 外观 设计 语言"]
    for m in (models or []):
        q.append(f"{m} 造型 设计")
    return q


def plan_from_generic(category: str | None, models: list[str] | None,
                      per_type: int = 2) -> dict:
    """把通用查询映射到确定性执行类型（review/industry），供兜底轮使用。"""
    qs = generic_queries(category, models)
    n = len(qs)
    cut = max(1, n // 2)
    return {
        "queries": {"industry": qs[:cut], "review": qs[cut:]},
        "quota": {"industry": min(per_type, cut),
                  "review": min(per_type, max(1, n - cut))},
    }
