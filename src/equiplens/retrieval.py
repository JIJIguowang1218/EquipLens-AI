"""检索模块 R0：检索计划配置解析（D12——检索由报告规划驱动，Agent 无自由意志）。

输入四要素: 检索类型 / 部件选择 / 页面类型+页数 / （测试期）名录清单
输出: 任务树 JSON（plan）。渠道执行（抓取）属 R1，本模块只负责"计划换算"。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from . import db as _db

PLAN_TYPES = ("full", "gap_fill", "part_focus")
PAGE_TEMPLATES = {
    # 素材需求模板（暂定，随 FR-4 报告规划模块细化）
    "vehicle_page": {
        "label": "竞品分析单车页",
        "key_views": ["hero_lf", "hero_rf", "side_l", "side_r"],   # L1 底线视角
        "front_parts": ["grille", "headlamp", "bumper"],           # 前脸部件组（L2 要求）
        "images_per_page": 6,
    },
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")


def _tid(kind: str) -> str:
    return f"t-{kind}-{uuid.uuid4().hex[:8]}"


def validate_config(config: dict) -> None:
    ptype = config.get("type")
    if ptype not in PLAN_TYPES:
        raise ValueError(f"检索类型非法: {ptype}（可选 {PLAN_TYPES}）")
    for pt in config.get("page_types", []):
        if pt.get("type") not in PAGE_TEMPLATES:
            raise ValueError(f"页面类型非法: {pt.get('type')}（可选 {list(PAGE_TEMPLATES)}）")
        if not isinstance(pt.get("pages"), int) or pt["pages"] < 1:
            raise ValueError(f"页数须为正整数: {pt}")
    if ptype == "part_focus" and not config.get("parts"):
        raise ValueError("部件专项检索必须指定 parts（vocab 词表 ID 列表）")
    if not config.get("vehicles"):
        raise ValueError("R0 阶段名录为人工给定，vehicles 不能为空（名录联网检索属 R2）")


def _gap_tasks_for_vehicle(conn, vehicle_id: str, parts: list[str]) -> dict:
    """从完备度与槽位状态推导该车的缺口任务内容（R3 补缺检索的计划基础）。"""
    comp = _db.completeness(conn, vehicle_id)
    missing_views: list[str] = []
    if comp["level"] == "L0":
        missing_views = list(PAGE_TEMPLATES["vehicle_page"]["key_views"])
    missing_parts = [p for p in parts
                     if _db.slot_state(conn, vehicle_id, p) in ("缺失", "有·待确认")]
    return {"missing_views": missing_views, "missing_parts": missing_parts}


def build_plan(config: dict, conn=None) -> dict:
    """配置 → 任务树。gap_fill 需要 conn（读完备度），其余类型可离线。"""
    validate_config(config)
    ptype = config["type"]
    vehicles = config["vehicles"]
    parts = list(config.get("parts") or [])

    # 页面类型 → 每车配额（D12: 页数 × 模板单页图数）
    quota = sum(PAGE_TEMPLATES[pt["type"]]["images_per_page"] * pt["pages"]
                for pt in config.get("page_types", [{"type": "vehicle_page", "pages": 1}]))

    plan = {
        "plan_id": f"plan-{uuid.uuid4().hex[:12]}",
        "type": ptype,
        "created_at": _now(),
        "vehicles": vehicles,
        "parts": parts,
        "page_types": config.get("page_types", [{"type": "vehicle_page", "pages": 1}]),
        "quota_per_vehicle": quota,
        "tasks": [],
    }
    tasks = plan["tasks"]

    if ptype == "full":
        tasks.append({"id": _tid("roster"), "kind": "roster",
                      "params": {"vehicles": vehicles, "category": config.get("category")}})
        for v in vehicles:
            tasks.append({"id": _tid("params"), "kind": "params", "vehicle": v})
            tasks.append({"id": _tid("images"), "kind": "images", "vehicle": v,
                          "parts": parts, "quota": quota})
    elif ptype == "part_focus":
        for p in parts:
            tasks.append({"id": _tid("part_images"), "kind": "part_images",
                          "part": p, "vehicles": vehicles, "quota": quota})
    elif ptype == "gap_fill":
        if conn is None:
            raise ValueError("gap_fill 需要连接数据库以读取完备度")
        for v in vehicles:
            gaps = _gap_tasks_for_vehicle(conn, v, parts or list(PAGE_TEMPLATES["vehicle_page"]["front_parts"]))
            tasks.append({"id": _tid("images"), "kind": "images", "vehicle": v,
                          "missing_views": gaps["missing_views"],
                          "missing_parts": gaps["missing_parts"], "quota": quota})
    return plan
