"""薄数据访问层：建库、导入/导出、确认/撤销、派生查询。

模块间只通过数据契约（本层 + JSON 包）交换，不互相调用。
"""

import json
import os
import sqlite3
from pathlib import Path

DDL_PATH = Path(__file__).resolve().parents[2] / "db" / "schema.sql"

TABLES = ["vocab", "vehicles", "assets", "sources", "facts", "descriptions", "confirm_log"]
JSON_COLUMNS = {
    "assets": {"crop_bbox", "quality_flags"},
    "descriptions": {"evidence_asset_ids", "source_ids"},
}


def connect(db_path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL_PATH.read_text(encoding="utf-8"))
    conn.commit()


# ---------------------------------------------------------------- 导入 / 导出

def _rows_to_dicts(table: str, rows) -> list[dict]:
    cols = set(JSON_COLUMNS.get(table, set()))
    out = []
    for r in rows:
        d = dict(r)
        for c in cols:
            if d.get(c) is not None:
                d[c] = json.loads(d[c])
        out.append(d)
    return out


def export_bundle(conn: sqlite3.Connection) -> dict:
    """导出为符合 equip-data.schema.json 的包；各表按 id 排序保证确定性。"""
    bundle = {}
    for t in TABLES:
        rows = conn.execute(f"SELECT * FROM {t} ORDER BY id").fetchall()
        bundle[t] = _rows_to_dicts(t, rows)
    bundle["meta"] = {"format_version": "0.1", "exported_at": _now()}
    return bundle


def import_bundle(conn: sqlite3.Connection, bundle: dict) -> None:
    """导入导出包。调用方须先用 JSON Schema 校验通过。"""
    order = ["vocab", "vehicles", "assets", "sources", "facts", "descriptions", "confirm_log"]
    # assets 内部先原图后裁图，满足自引用外键
    assets = sorted(bundle["assets"], key=lambda a: (a["kind"] != "source_image", a["id"]))
    for t in order:
        rows = list(bundle[t])
        if t == "assets":
            rows = assets
        for rec in rows:
            d = dict(rec)
            for c in JSON_COLUMNS.get(t, set()):
                if d.get(c) is not None:
                    d[c] = json.dumps(d[c], ensure_ascii=False)
            cols = ", ".join(d.keys())
            ph = ", ".join("?" for _ in d)
            conn.execute(f"INSERT INTO {t} ({cols}) VALUES ({ph})", list(d.values()))
    conn.commit()


# ---------------------------------------------------------------- 确认 / 撤销

TABLE_FOR_OBJECT = {"vehicle": "vehicles", "asset": "assets", "source": "sources",
                    "fact": "facts", "description": "descriptions"}


def _now() -> str:
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")


def _uuid() -> str:
    import uuid
    return str(uuid.uuid4())


def confirm(conn, object_type: str, object_id: str, field: str,
            machine_value, confirmed_value, method: str, op_id: str,
            confirmed_by: str = "user", at: str | None = None) -> str:
    """写一条确认日志并覆盖目标字段。machine_value 必须是覆盖前的现值（由调用方传入，测试负例可故意传错以验证审计）。"""
    table = TABLE_FOR_OBJECT[object_type]
    cur = conn.execute(f"SELECT {field} FROM {table} WHERE id = ?", (object_id,))
    row = cur.fetchone()
    if row is None:
        raise ValueError(f"{object_type} {object_id} 不存在")
    log_id = _uuid()
    conn.execute(
        "INSERT INTO confirm_log (id, op_id, object_type, object_id, field, machine_value,"
        " confirmed_value, method, confirmed_at, confirmed_by) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (log_id, op_id, object_type, object_id, field,
         json.dumps(machine_value, ensure_ascii=False),
         json.dumps(confirmed_value, ensure_ascii=False),
         method, at or _now(), confirmed_by))
    conn.execute(f"UPDATE {table} SET {field} = ?, updated_at = ? WHERE id = ?",
                 (json.dumps(confirmed_value, ensure_ascii=False)
                  if field in JSON_COLUMNS.get(table, set()) else confirmed_value,
                  at or _now(), object_id))
    conn.commit()
    return log_id


def undo(conn, log_id: str) -> None:
    """撤销 = 恢复机器原值。日志本身不动（只增不改）。"""
    row = conn.execute("SELECT * FROM confirm_log WHERE id = ?", (log_id,)).fetchone()
    if row is None:
        raise ValueError(f"确认记录 {log_id} 不存在")
    table = TABLE_FOR_OBJECT[row["object_type"]]
    value = json.loads(row["machine_value"])
    conn.execute(f"UPDATE {table} SET {row['field']} = ?, updated_at = ? WHERE id = ?",
                 (json.dumps(value, ensure_ascii=False)
                  if row["field"] in JSON_COLUMNS.get(table, set()) else value,
                  _now(), row["object_id"]))
    conn.commit()


# ---------------------------------------------------------------- 文件不变量

def save_original(data_dir: Path, vehicle_id: str, asset_id: str, ext: str, data: bytes) -> Path:
    """写入原图；目标已存在即拒绝（原图不可变）。返回相对 data_dir 的路径。"""
    rel = f"assets/{vehicle_id}/originals/{asset_id}.{ext}"
    dest = Path(data_dir) / rel
    if dest.exists():
        raise FileExistsError(f"原图不可覆盖: {rel}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return Path(rel)


def save_crop(data_dir: Path, vehicle_id: str, asset_id: str, ext: str, data: bytes) -> Path:
    rel = f"assets/{vehicle_id}/crops/{asset_id}.{ext}"
    dest = Path(data_dir) / rel
    if dest.exists():
        raise FileExistsError(f"文件已存在: {rel}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return Path(rel)


# ---------------------------------------------------------------- 派生查询（只查不存）

L1_VIEWS = ("hero_lf", "hero_rf", "side_l", "side_r")
FRONT_PARTS = ("bumper", "headlamp", "grille")


def _confirmed_assets(conn, vehicle_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM assets WHERE vehicle_id = ? AND binding_status = 'confirmed'"
        " AND confirm_status = 'confirmed'", (vehicle_id,)).fetchall()


def completeness(conn, vehicle_id: str) -> dict:
    """完备度 L0–L3（规范 §6）。返回 {"level": str, "reasons": [...]}。"""
    rows = _confirmed_assets(conn, vehicle_id)
    views = {r["view_angle"] for r in rows}
    crops = [r for r in rows if r["kind"] == "crop" and r["part_id"]]
    crop_parts = {r["part_id"] for r in crops}
    front_face = bool(crop_parts & set(FRONT_PARTS))

    has_hero = bool(views & {"hero_lf", "hero_rf"})
    has_side = bool(views & {"side_l", "side_r"})
    has_front = "front" in views
    has_rear = "rear" in views
    has_interior = "interior" in views

    if not (has_hero or has_side):
        return {"level": "L0", "reasons": ["无已确认主视角或正侧素材"]}
    level, reasons = "L1", ["有主视角或正侧"]
    if (has_front or has_rear) and len(crops) >= 2 and front_face:
        level = "L2"
        reasons.append("有正前/正后 + 带部位裁图>=2 且含前脸组")
    else:
        return {"level": level, "reasons": reasons}
    if has_front and has_rear and has_side and has_interior and len(crops) >= 4:
        level = "L3"
        reasons.append("三向+内饰齐, 裁图>=4")
    return {"level": level, "reasons": reasons}


def slot_state(conn, vehicle_id: str, part_id: str) -> str:
    """部位槽位状态: 有·已确认 / 有·待确认 / 缺失（派生查询）。"""
    row = conn.execute(
        "SELECT confirm_status, binding_status FROM assets WHERE vehicle_id = ? AND part_id = ?"
        " AND kind = 'crop' ORDER BY CASE confirm_status WHEN 'confirmed' THEN 0 ELSE 1 END",
        (vehicle_id, part_id)).fetchone()
    if row is None:
        return "缺失"
    if row["confirm_status"] == "confirmed" and row["binding_status"] == "confirmed":
        return "有·已确认"
    return "有·待确认"


def unbound_pool(conn) -> list[sqlite3.Row]:
    """待归号池 = binding_status='unbound' 的素材（PRD FR-1.1 待确认分组）。"""
    return conn.execute("SELECT * FROM assets WHERE binding_status = 'unbound' ORDER BY id").fetchall()


def assets_for_vehicle(conn, vehicle_id: str, only_confirmed: bool = False) -> list[sqlite3.Row]:
    sql = "SELECT * FROM assets WHERE vehicle_id = ?"
    if only_confirmed:
        sql += " AND confirm_status = 'confirmed'"
    return conn.execute(sql + " ORDER BY id", (vehicle_id,)).fetchall()


def descriptions_query(conn, vehicle_id: str | None = None, node_type: str | None = None,
                       part_id: str | None = None, axis_type: str | None = None,
                       scope: str | None = None, only_confirmed: bool = False) -> list[sqlite3.Row]:
    """三轴查询：报告页型 = 对描述档案的一次查询（规范 §1 D4）。"""
    sql, params = "SELECT * FROM descriptions WHERE 1=1", []
    if vehicle_id:
        sql += " AND vehicle_id = ?"; params.append(vehicle_id)
    if node_type:
        sql += " AND node_type = ?"; params.append(node_type)
    if part_id:
        sql += " AND part_id = ?"; params.append(part_id)
    if axis_type:
        sql += " AND axis_type = ?"; params.append(axis_type)
    if scope:
        sql += " AND scope = ?"; params.append(scope)
    if only_confirmed:
        sql += " AND confirm_status = 'confirmed'"
    return conn.execute(sql + " ORDER BY id", params).fetchall()


def find_asset_by_hash(conn, hash_sha256: str) -> sqlite3.Row | None:
    """同图判重入口（D5）：文件哈希精确匹配。"""
    return conn.execute("SELECT * FROM assets WHERE hash_sha256 = ?", (hash_sha256,)).fetchone()


def set_hero(conn, vehicle_id: str, asset_id: str) -> None:
    row = conn.execute("SELECT vehicle_id, kind, view_angle FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if row is None:
        raise ValueError(f"素材 {asset_id} 不存在")
    if row["vehicle_id"] != vehicle_id or row["view_angle"] not in ("hero_lf", "hero_rf"):
        raise ValueError("主图必须是该车已对号的 3/4 主视角素材")
    conn.execute("UPDATE vehicles SET hero_asset_id = ? WHERE id = ?", (asset_id, vehicle_id))
    conn.commit()
