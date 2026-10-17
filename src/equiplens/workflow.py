"""M2 确认工作流：车型管理 / 对号 / 打标确认 / 拒绝 / 裁图 / 车型摘要。

原则: 一切人工操作经 confirm_many() 落账——机器原值=操作前状态, 撤销=按操作号整体恢复,
账本(confirm_log)只增不改。对号 = 车辆+状态+证据三字段原子变更。
"""

from __future__ import annotations

import json
import uuid
import hashlib
from io import BytesIO
from pathlib import Path

from PIL import Image

from . import db
from .db import _now

VALID_VIEWS = ("hero_lf", "hero_rf", "front", "rear", "side_l", "side_r",
               "ortho_sheet", "detail", "interior", "scene", "nameplate")


def _op() -> str:
    return f"op-{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------- 车型管理

def create_vehicle(conn, brand: str, model_name: str, category: str | None = None,
                   generation: str | None = None) -> str:
    vid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO vehicles (id, brand, model_name, category, generation, list_status,"
        " hero_asset_id, project_id, created_at) VALUES (?,?,?,?,?,'candidate',NULL,NULL,?)",
        (vid, brand, model_name, category, generation, _now()))
    conn.commit()
    return vid


def lock_vehicle(conn, vehicle_id: str) -> str:
    row = conn.execute("SELECT list_status FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
    if row is None:
        raise ValueError(f"车型 {vehicle_id} 不存在")
    return db.confirm(conn, "vehicle", vehicle_id, "list_status",
                      row["list_status"], "locked", method="single", op_id=_op())


# ---------------------------------------------------------------- 对号 / 退回

def bind_asset(conn, asset_id: str, vehicle_id: str, method: str = "single") -> str:
    """对号: unbound → confirmed, 证据=human。三字段一次操作原子落账。"""
    a = conn.execute("SELECT vehicle_id, binding_status, binding_evidence FROM assets WHERE id = ?",
                     (asset_id,)).fetchone()
    if a is None:
        raise ValueError(f"素材 {asset_id} 不存在")
    if a["binding_status"] != "unbound":
        raise ValueError(f"素材 {asset_id} 不在待归号池(当前 {a['binding_status']})")
    if conn.execute("SELECT 1 FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone() is None:
        raise ValueError(f"车型 {vehicle_id} 不存在")
    return db.confirm_many(conn, [
        ("asset", asset_id, "vehicle_id", None, vehicle_id),
        ("asset", asset_id, "binding_status", "unbound", "confirmed"),
        ("asset", asset_id, "binding_evidence", "none", "human"),
    ], op_id=_op(), method=method)


def _hero_clear_entries(conn, asset_id: str) -> list[tuple]:
    """素材失效(拒绝/退回)时, 若它是某车主图, 生成清空指针的确认条目(M3.1 漏洞①修复)。"""
    rows = conn.execute("SELECT id, hero_asset_id FROM vehicles WHERE hero_asset_id = ?",
                        (asset_id,)).fetchall()
    return [("vehicle", r["id"], "hero_asset_id", r["hero_asset_id"], None) for r in rows]


def unbind_asset(conn, asset_id: str) -> str:
    """退回待归号池（对号的逆操作, 同样落账; 若为主图则联动清空指针）。"""
    a = conn.execute("SELECT vehicle_id, binding_status, binding_evidence FROM assets WHERE id = ?",
                     (asset_id,)).fetchone()
    if a is None or a["binding_status"] == "unbound":
        raise ValueError(f"素材 {asset_id} 不处于已对号状态")
    return db.confirm_many(conn, [
        ("asset", asset_id, "vehicle_id", a["vehicle_id"], None),
        ("asset", asset_id, "binding_status", a["binding_status"], "unbound"),
        ("asset", asset_id, "binding_evidence", a["binding_evidence"], "none"),
    ] + _hero_clear_entries(conn, asset_id), op_id=_op(), method="single")


# ---------------------------------------------------------------- 打标 / 拒绝

def set_view(conn, asset_id: str, view_angle: str, method: str = "single",
             op_id: str | None = None) -> str:
    if view_angle not in VALID_VIEWS:
        raise ValueError(f"非法视角: {view_angle}")
    row = conn.execute("SELECT view_angle FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if row is None:
        raise ValueError(f"素材 {asset_id} 不存在")
    return db.confirm(conn, "asset", asset_id, "view_angle",
                      row["view_angle"], view_angle, method=method,
                      op_id=op_id or _op())


def batch_set_view(conn, items: list[tuple[str, str]]) -> str:
    """批量视角打标: [(asset_id, view_angle), ...] 共用一个操作号, 逐条可撤销。"""
    ops = []
    for asset_id, view in items:
        row = conn.execute("SELECT view_angle FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if row is None:
            raise ValueError(f"素材 {asset_id} 不存在")
        if view not in VALID_VIEWS:
            raise ValueError(f"非法视角: {view}")
        ops.append(("asset", asset_id, "view_angle", row["view_angle"], view))
    return db.confirm_many(conn, ops, op_id=_op(), method="batch")


def reject_asset(conn, asset_id: str) -> str:
    row = conn.execute("SELECT confirm_status FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if row is None:
        raise ValueError(f"素材 {asset_id} 不存在")
    return db.confirm_many(conn, [
        ("asset", asset_id, "confirm_status", row["confirm_status"], "rejected"),
    ] + _hero_clear_entries(conn, asset_id), op_id=_op(), method="single")


# ---------------------------------------------------------------- 裁图（内生, T1 自证）

def crop_asset(conn, data_dir: Path, source_asset_id: str, bbox: dict, part_id: str) -> str:
    """从已对号原图裁出部件特写: 父子关系由构造自证(证据=self_derived), bbox 必记。"""
    src = conn.execute(
        "SELECT * FROM assets WHERE id = ?", (source_asset_id,)).fetchone()
    if src is None:
        raise ValueError(f"源素材 {source_asset_id} 不存在")
    if src["kind"] != "source_image":
        raise ValueError("只允许从原图裁, 不允许从裁图再裁(规范 D1)")
    if src["binding_status"] != "confirmed":
        raise ValueError("只从已对号原图裁(先对号再裁图)")
    if not (0 <= bbox["x"] and 0 <= bbox["y"]
            and bbox["x"] + bbox["w"] <= (src["width"] or 0)
            and bbox["y"] + bbox["h"] <= (src["height"] or 0)):
        raise ValueError(f"bbox 越界: 原图 {src['width']}x{src['height']}, bbox={bbox}")
    if conn.execute("SELECT 1 FROM vocab WHERE id = ?", (part_id,)).fetchone() is None:
        raise ValueError(f"部位 {part_id} 不在词表")

    img = Image.open(Path(data_dir) / src["file_path"])
    piece = img.crop((bbox["x"], bbox["y"], bbox["x"] + bbox["w"], bbox["y"] + bbox["h"]))
    buf = BytesIO()
    piece.save(buf, format="PNG")
    asset_id = str(uuid.uuid4())
    rel = db.save_crop(Path(data_dir), src["vehicle_id"], asset_id, "png", buf.getvalue())
    conn.execute(
        "INSERT INTO assets (id, vehicle_id, binding_status, binding_evidence, kind,"
        " parent_asset_id, crop_bbox, file_path, view_angle, asset_nature, part_id,"
        " width, height, quality_flags, hash_sha256, phash, confirm_status, notes,"
        " created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (asset_id, src["vehicle_id"], "confirmed", "self_derived", "crop",
         source_asset_id, json.dumps(bbox), rel, "detail", src["asset_nature"], part_id,
         bbox["w"], bbox["h"], "[]", hashlib.sha256(buf.getvalue()).hexdigest(),
         None, "machine_tagged", None, _now(), _now()))
    conn.commit()
    return asset_id


# ---------------------------------------------------------------- 变体链接（D10）

def link_variants(conn, asset_ids: list[str]) -> str:
    """人工确认互为同图变体后归组: 共享一个 variant_group UUID, 可撤销, 全程落账。"""
    if len(asset_ids) < 2:
        raise ValueError("变体分组至少需要 2 个素材")
    group = str(uuid.uuid4())
    ops = []
    for aid in asset_ids:
        row = conn.execute("SELECT variant_group, confirm_status FROM assets WHERE id = ?",
                           (aid,)).fetchone()
        if row is None:
            raise ValueError(f"素材 {aid} 不存在")
        if row["confirm_status"] == "rejected":
            raise ValueError(f"被拒素材不得入组: {aid}")
        ops.append(("asset", aid, "variant_group", row["variant_group"], group))
    return db.confirm_many(conn, ops, op_id=_op(), method="single")


def unlink_variant(conn, asset_id: str) -> str:
    row = conn.execute("SELECT variant_group FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if row is None:
        raise ValueError(f"素材 {asset_id} 不存在")
    if row["variant_group"] is None:
        raise ValueError(f"素材 {asset_id} 不在任何变体分组")
    return db.confirm(conn, "asset", asset_id, "variant_group",
                      row["variant_group"], None, method="single", op_id=_op())


# ---------------------------------------------------------------- 查询视图

def vehicle_summary(conn, vehicle_id: str) -> dict:
    """车型摘要: 渐进披露列表层的数据接口。"""
    v = conn.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
    if v is None:
        raise ValueError(f"车型 {vehicle_id} 不存在")
    assets = db.assets_for_vehicle(conn, vehicle_id)
    counts = {"confirmed": 0, "machine_tagged": 0, "rejected": 0}
    pending = []
    for a in assets:
        counts[a["confirm_status"]] = counts.get(a["confirm_status"], 0) + 1
        if a["confirm_status"] == "machine_tagged" and a["confirm_status"] != "rejected":
            pending.append(a["id"])
    return {
        "vehicle": {"id": v["id"], "brand": v["brand"], "model_name": v["model_name"],
                    "generation": v["generation"], "list_status": v["list_status"]},
        "hero_asset_id": v["hero_asset_id"],
        "asset_counts": counts,
        "completeness": db.completeness(conn, vehicle_id),
        "pending_confirm": pending,
    }
