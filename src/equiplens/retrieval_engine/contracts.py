"""检索中契约：任务单 / 目标 / 资产 / 核验 / 策略。

P0 只做“读得进来、校验得了、能序列化”，不做检索。
所有结构都能 JSON 往返，方便写进检查点和事件。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VALID_TIERS = ("exact", "environment", "platform", "cross")
VALID_RELEVANCE = ("strong", "conditional", "none")
VALID_ACCEPT = ("A", "B", "C")


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(x) for x in value]


@dataclass
class PartRequirement:
    part: str
    label: str = ""
    location: str = ""
    design_relevance: str = "none"
    views: tuple[str, ...] = ()
    accept: str = "A"
    mechanism: tuple[str, ...] = ()
    # L1.5 / task-brief v2 的分析字段：不参与引擎检索，但必须随 brief 保留
    kind: str = "part"
    part_family: str = ""
    taxonomy_status: str = "known"
    relation_axis: str = "exact"
    design_axes: tuple[str, ...] = ()
    why: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "PartRequirement":
        return cls(
            part=str(data["part"]),
            label=str(data.get("label") or data["part"]),
            location=str(data.get("location") or ""),
            design_relevance=str(data.get("design_relevance") or "none"),
            views=tuple(_as_list(data.get("views"))),
            accept=str(data.get("accept") or "A"),
            mechanism=tuple(_as_list(data.get("mechanism"))),
            kind=str(data.get("kind") or "part"),
            part_family=str(data.get("part_family") or ""),
            taxonomy_status=str(data.get("taxonomy_status") or "known"),
            relation_axis=str(data.get("relation_axis") or "exact"),
            design_axes=tuple(_as_list(data.get("design_axes"))),
            why=str(data.get("why") or ""),
        )

    def to_dict(self) -> dict:
        return {
            "part": self.part,
            "label": self.label,
            "location": self.location,
            "design_relevance": self.design_relevance,
            "views": list(self.views),
            "accept": self.accept,
            "mechanism": list(self.mechanism),
            "kind": self.kind,
            "part_family": self.part_family,
            "taxonomy_status": self.taxonomy_status,
            "relation_axis": self.relation_axis,
            "design_axes": list(self.design_axes),
            "why": self.why,
        }


@dataclass
class ResearchUnit:
    unit_id: str
    tier: str
    scope: str
    parts: tuple[str, ...]
    quota: int
    budget: dict = field(default_factory=dict)
    stop: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchUnit":
        return cls(
            unit_id=str(data["unit_id"]),
            tier=str(data.get("tier") or "exact"),
            scope=str(data.get("scope") or ""),
            parts=tuple(_as_list(data.get("parts"))),
            quota=int(data.get("quota") or 1),
            budget=dict(data.get("budget") or {}),
            stop=str(data.get("stop") or ""),
        )

    def to_dict(self) -> dict:
        return {
            "unit_id": self.unit_id,
            "tier": self.tier,
            "scope": self.scope,
            "parts": list(self.parts),
            "quota": self.quota,
            "budget": dict(self.budget),
            "stop": self.stop,
        }


@dataclass
class Brief:
    brief_id: str
    request: dict
    part_requirements: list[PartRequirement]
    research_units: list[ResearchUnit]
    tiers: list[str]
    budget: dict
    stop_rules: dict
    negative: list[str]
    strategy_ref: str
    assumptions: list[dict] = field(default_factory=list)
    region_requirements: list[dict] = field(default_factory=list)

    @property
    def parts_by_key(self) -> dict[str, PartRequirement]:
        return {p.part: p for p in self.part_requirements}

    @property
    def vehicle_slots(self) -> int:
        return int((self.request.get("page_budget") or {}).get("vehicle_slots") or 0)

    @property
    def backup_slots(self) -> int:
        """交付备选台数：默认 4；显式写 0 表示不要求备选（测试/特殊任务单）。"""
        value = (self.request.get("page_budget") or {}).get("backup_slots")
        return 4 if value is None else max(0, int(value))

    @classmethod
    def from_dict(cls, data: dict) -> "Brief":
        return cls(
            brief_id=str(data["brief_id"]),
            request=dict(data.get("request") or {}),
            part_requirements=[PartRequirement.from_dict(x)
                               for x in data.get("part_requirements", [])],
            research_units=[ResearchUnit.from_dict(x)
                            for x in data.get("research_units", [])],
            tiers=[str(x) for x in data.get("tiers", [])],
            budget=dict(data.get("budget") or {}),
            stop_rules=dict(data.get("stop_rules") or {}),
            negative=_as_list(data.get("negative")),
            strategy_ref=str(data.get("strategy_ref") or ""),
            assumptions=[dict(x) for x in data.get("assumptions", [])],
            region_requirements=[dict(x) for x in data.get("region_requirements", [])],
        )

    def to_dict(self) -> dict:
        return {
            "brief_id": self.brief_id,
            "request": dict(self.request),
            "part_requirements": [p.to_dict() for p in self.part_requirements],
            "research_units": [u.to_dict() for u in self.research_units],
            "tiers": list(self.tiers),
            "budget": dict(self.budget),
            "stop_rules": dict(self.stop_rules),
            "negative": list(self.negative),
            "strategy_ref": self.strategy_ref,
            "assumptions": list(self.assumptions),
            "region_requirements": list(self.region_requirements),
        }


@dataclass
class Target:
    target_id: str
    model: str
    source: str
    tier: str
    parts: tuple[str, ...]
    unit_id: str = ""
    sources: tuple[str, ...] = ()
    citation_ok: bool = False
    query: str = ""
    identity_kind: str = ""   # code / series / generic（只标记，不参与淘汰）
    intent_rank: int = 0      # 1 = 最想交付（LLM 先验，不是图片质量）
    intent_band: str = ""     # must / strong / possible / weak
    intent_reason: str = ""
    role: str = ""            # primary / backup / pool
    pinned: bool = False      # 用户指定必须保留
    part_only: bool = False   # FILL 打的软标记：有 scene 元数据但没有 single_vehicle
                              # （2026-11-12 决策：只标记、不拒绝；见 docs/P0-REVIEW）

    @classmethod
    def from_dict(cls, data: dict, *, source: str, tier: str) -> "Target":
        return cls(
            target_id=str(data["target_id"]),
            model=str(data.get("model") or data["target_id"]),
            source=source,
            tier=tier,
            parts=tuple(_as_list(data.get("parts"))),
            unit_id=str(data.get("unit_id") or ""),
            sources=tuple(_as_list(data.get("sources"))),
            citation_ok=bool(data.get("citation_ok")),
            query=str(data.get("query") or ""),
            identity_kind=str(data.get("identity_kind") or ""),
            intent_rank=int(data.get("intent_rank") or 0),
            intent_band=str(data.get("intent_band") or ""),
            intent_reason=str(data.get("intent_reason") or ""),
            role=str(data.get("role") or ""),
            pinned=bool(data.get("pinned")),
            part_only=bool(data.get("part_only")),
        )

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "model": self.model,
            "source": self.source,
            "tier": self.tier,
            "parts": list(self.parts),
            "unit_id": self.unit_id,
            "sources": list(self.sources),
            "citation_ok": self.citation_ok,
            "query": self.query,
            "identity_kind": self.identity_kind,
            "intent_rank": self.intent_rank,
            "intent_band": self.intent_band,
            "intent_reason": self.intent_reason,
            "role": self.role,
            "pinned": self.pinned,
            "part_only": self.part_only,
        }


@dataclass
class Asset:
    asset_id: str
    target_id: str
    part: str
    view: str = ""
    width: int = 0
    height: int = 0
    url: str = ""
    title: str = ""
    model: str = ""
    channel: str = ""
    status: str = ""
    scene: str = ""
    overview: bool = False
    # 这张图的来源查询档位（待办A）：exact=窄查询精确命中，model=车型全名，
    # alias=中文别名改写，part_fallback=部件+车型兜底。用于区分“回退来源”的图。
    query_tier: str = ""
    source_query: str = ""

    @classmethod
    def from_dict(cls, data: dict, *, target_id: str, part: str) -> "Asset":
        return cls(
            asset_id=str(data["asset_id"]),
            target_id=target_id,
            part=part,
            view=str(data.get("view") or ""),
            width=int(data.get("width") or 0),
            height=int(data.get("height") or 0),
            url=str(data.get("url") or ""),
            title=str(data.get("title") or ""),
            model=str(data.get("model") or ""),
            channel=str(data.get("channel") or ""),
            status=str(data.get("status") or ""),
            scene=str(data.get("scene") or ""),
            overview=bool(data.get("overview")),
            query_tier=str(data.get("query_tier") or ""),
            source_query=str(data.get("source_query") or ""),
        )

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "target_id": self.target_id,
            "part": self.part,
            "view": self.view,
            "width": self.width,
            "height": self.height,
            "url": self.url,
            "title": self.title,
            "model": self.model,
            "channel": self.channel,
            "status": self.status,
            "scene": self.scene,
            "overview": self.overview,
            "query_tier": self.query_tier,
            "source_query": self.source_query,
        }


@dataclass
class Verification:
    accepted: bool
    identity: str = "unknown"
    visibility: str = "unknown"
    origin: str = "unknown"
    grade: str = ""
    defects: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict) -> "Verification":
        return cls(
            accepted=bool(data.get("accepted")),
            identity=str(data.get("identity") or "unknown"),
            visibility=str(data.get("visibility") or "unknown"),
            origin=str(data.get("origin") or "unknown"),
            grade=str(data.get("grade") or ""),
            defects=tuple(_as_list(data.get("defects"))),
            warnings=tuple(_as_list(data.get("warnings"))),
        )

    def to_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "identity": self.identity,
            "visibility": self.visibility,
            "origin": self.origin,
            "grade": self.grade,
            "defects": list(self.defects),
            "warnings": list(self.warnings),
        }


def validate_brief(data: dict) -> list[str]:
    """返回错误列表；空列表表示通过。"""
    errors: list[str] = []
    for key in ("brief_id", "request", "part_requirements", "research_units",
                "tiers", "strategy_ref"):
        if key not in data:
            errors.append(f"missing:{key}")
    if errors:
        return errors

    request = data.get("request") or {}
    if not request.get("class"):
        errors.append("request.class 不能为空")
    page_budget = request.get("page_budget") or {}
    if int(page_budget.get("vehicle_slots") or 0) <= 0:
        errors.append("request.page_budget.vehicle_slots 必须 > 0")

    parts = data.get("part_requirements") or []
    if not parts:
        errors.append("part_requirements 不能为空")
    part_keys = [str(p.get("part")) for p in parts]
    if len(part_keys) != len(set(part_keys)):
        errors.append("part_requirements 存在重复 part")
    for p in parts:
        if p.get("design_relevance") not in VALID_RELEVANCE:
            errors.append(f"part {p.get('part')}: design_relevance 非法")
        if p.get("accept") not in VALID_ACCEPT:
            errors.append(f"part {p.get('part')}: accept 非法")

    units = data.get("research_units") or []
    if not units:
        errors.append("research_units 不能为空")
    known = set(part_keys)
    unit_ids = [str(u.get("unit_id")) for u in units]
    if len(unit_ids) != len(set(unit_ids)):
        errors.append("research_units 存在重复 unit_id")
    for u in units:
        if u.get("tier") not in VALID_TIERS:
            errors.append(f"unit {u.get('unit_id')}: tier 非法")
        if int(u.get("quota") or 0) <= 0:
            errors.append(f"unit {u.get('unit_id')}: quota 必须 > 0")
        for part in _as_list(u.get("parts")):
            if part not in known:
                errors.append(f"unit {u.get('unit_id')}: 未知 part {part}")

    tiers = data.get("tiers") or []
    if not tiers:
        errors.append("tiers 不能为空")
    for t in tiers:
        if t not in VALID_TIERS:
            errors.append(f"tier 非法: {t}")
    return errors


def load_brief(path: str | Path) -> Brief:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_brief(data)
    if errors:
        raise ValueError("; ".join(errors))
    return Brief.from_dict(data)


