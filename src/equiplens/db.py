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
    """幂等建库 + 增量迁移: 已有表结构则跳过建表, 仅补差异（支持同一数据目录多次运行与旧库升级）。"""
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'vocab'").fetchone()
    if not exists:
        conn.executescript(DDL_PATH.read_text(encoding="utf-8"))
        conn.commit()
    _migrate(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    """旧库无损升级（规范 v0.2）: 补 variant_group 列; vocab 状态加 pending;
    confirm_log 对象类型加 vocab。全部为保数据重建/加列, 幂等。"""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(assets)")}
    if "variant_group" not in cols:
        conn.execute("ALTER TABLE assets ADD COLUMN variant_group TEXT")
    # 确认机制统一更新 updated_at, 补齐缺失该列的表
    for table in ("vehicles", "sources"):
        tcols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        if "updated_at" not in tcols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN updated_at TEXT")
    scols = {r[1] for r in conn.execute("PRAGMA table_info(sources)")}
    if "batch_id" not in scols:
        conn.execute("ALTER TABLE sources ADD COLUMN batch_id TEXT")  # D14 检索批次

    # v0.2.3: view_angle 枚举扩展 hero_45/side(方向未定态) —— CHECK 在表定义中, 重建迁移
    assets_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='assets'").fetchone()["sql"]
    if "'hero_45'" not in assets_sql:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.executescript("""
            DROP TABLE IF EXISTS assets_new;
            CREATE TABLE assets_new (
                id TEXT PRIMARY KEY,
                vehicle_id TEXT REFERENCES vehicles(id),
                binding_status TEXT NOT NULL CHECK (binding_status IN ('unbound','provisional','confirmed')),
                binding_evidence TEXT NOT NULL CHECK (binding_evidence IN ('none','self_derived','region_match','co_occurrence_labeled','co_occurrence_only','human')),
                kind TEXT NOT NULL CHECK (kind IN ('source_image','crop')),
                parent_asset_id TEXT REFERENCES assets_new(id),
                crop_bbox TEXT,
                file_path TEXT NOT NULL,
                view_angle TEXT NOT NULL CHECK (view_angle IN ('untagged','hero_45','hero_lf','hero_rf','front','rear','side','side_l','side_r','ortho_sheet','detail','interior','scene','nameplate')),
                asset_nature TEXT NOT NULL CHECK (asset_nature IN ('untagged','render','official_photo','real_photo','report_screenshot')),
                part_id TEXT REFERENCES vocab(id),
                width INTEGER, height INTEGER, quality_flags TEXT,
                hash_sha256 TEXT NOT NULL CHECK (length(hash_sha256) = 64),
                phash TEXT CHECK (phash IS NULL OR length(phash) = 16),
                confirm_status TEXT NOT NULL CHECK (confirm_status IN ('machine_tagged','confirmed','rejected')),
                variant_group TEXT, notes TEXT,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                CHECK ((kind = 'crop') = (parent_asset_id IS NOT NULL AND crop_bbox IS NOT NULL)),
                CHECK ((vehicle_id IS NULL) = (binding_status = 'unbound')),
                CHECK ((binding_evidence = 'none') = (binding_status = 'unbound'))
            );
            INSERT INTO assets_new (id, vehicle_id, binding_status, binding_evidence, kind,
                parent_asset_id, crop_bbox, file_path, view_angle, asset_nature, part_id,
                width, height, quality_flags, hash_sha256, phash, confirm_status,
                variant_group, notes, created_at, updated_at)
                SELECT id, vehicle_id, binding_status, binding_evidence, kind,
                parent_asset_id, crop_bbox, file_path, view_angle, asset_nature, part_id,
                width, height, quality_flags, hash_sha256, phash, confirm_status,
                variant_group, notes, created_at,
                COALESCE(updated_at, created_at, '1970-01-01T00:00:00+08:00') FROM assets;
            DROP TABLE assets;
            ALTER TABLE assets_new RENAME TO assets;
            CREATE INDEX idx_assets_vehicle ON assets(vehicle_id);
            CREATE INDEX idx_assets_parent ON assets(parent_asset_id);
        """)
        conn.execute("PRAGMA foreign_keys = ON")
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == [], "assets 迁移后外键校验失败"
    conn.commit()

    vocab_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='vocab'").fetchone()["sql"]
    if "'pending'" not in vocab_sql:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.executescript("""
            CREATE TABLE vocab_new (id TEXT PRIMARY KEY, type TEXT NOT NULL CHECK (type IN ('part')),
                term TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','active','retired')),
                note TEXT, updated_at TEXT, UNIQUE (type, term));
            INSERT INTO vocab_new (id, type, term, status, note, updated_at)
                SELECT id, type, term, status, note, NULL FROM vocab;
            DROP TABLE vocab;
            ALTER TABLE vocab_new RENAME TO vocab;
        """)
        conn.execute("PRAGMA foreign_keys = ON")
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == [], "迁移后外键校验失败"

    log_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='confirm_log'").fetchone()["sql"]
    if "'vocab'" not in log_sql:
        conn.executescript("""
            DROP TRIGGER IF EXISTS confirm_log_no_update;
            DROP TRIGGER IF EXISTS confirm_log_no_delete;
            CREATE TABLE confirm_log_new (id TEXT PRIMARY KEY, op_id TEXT NOT NULL,
                object_type TEXT NOT NULL CHECK (object_type IN ('vehicle','asset','source','fact','description','vocab')),
                object_id TEXT NOT NULL, field TEXT NOT NULL,
                machine_value TEXT NOT NULL, confirmed_value TEXT NOT NULL,
                method TEXT NOT NULL CHECK (method IN ('single','batch','auto')),
                confirmed_at TEXT NOT NULL, confirmed_by TEXT NOT NULL DEFAULT 'user');
            INSERT INTO confirm_log_new SELECT * FROM confirm_log;
            DROP TABLE confirm_log;
            ALTER TABLE confirm_log_new RENAME TO confirm_log;
            CREATE TRIGGER confirm_log_no_update BEFORE UPDATE ON confirm_log
                BEGIN SELECT RAISE(ABORT, 'confirm_log is append-only'); END;
            CREATE TRIGGER confirm_log_no_delete BEFORE DELETE ON confirm_log
                BEGIN SELECT RAISE(ABORT, 'confirm_log is append-only'); END;
            CREATE INDEX idx_log_object ON confirm_log(object_type, object_id);
        """)
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
                    "fact": "facts", "description": "descriptions", "vocab": "vocab"}


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
    return confirm_many(conn, [(object_type, object_id, field, machine_value, confirmed_value)],
                        op_id=op_id, method=method, confirmed_by=confirmed_by, at=at)


def confirm_many(conn, ops: list[tuple], op_id: str, method: str = "single",
                 confirmed_by: str = "user", at: str | None = None) -> str:
    """一个操作号下原子地写多条确认日志并覆盖多个字段（如对号 = 车辆+状态+证据三字段）。

    ops: [(object_type, object_id, field, machine_value, confirmed_value), ...]
    单事务提交, 避免多字段操作中途失败造成违反 CHECK 的中间态。
    """
    import uuid as _uuid
    ts = at or _now()
    for object_type, object_id, field, machine_value, confirmed_value in ops:
        table = TABLE_FOR_OBJECT[object_type]
        if conn.execute(f"SELECT 1 FROM {table} WHERE id = ?", (object_id,)).fetchone() is None:
            raise ValueError(f"{object_type} {object_id} 不存在")
        conn.execute(
            "INSERT INTO confirm_log (id, op_id, object_type, object_id, field, machine_value,"
            " confirmed_value, method, confirmed_at, confirmed_by) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (str(_uuid.uuid4()), op_id, object_type, object_id, field,
             json.dumps(machine_value, ensure_ascii=False),
             json.dumps(confirmed_value, ensure_ascii=False), method, ts, confirmed_by))
    # 多字段联动(如对号=车辆+状态+证据)的中间态必然违反耦合 CHECK——
    # 更新期间挂起 CHECK(仅本连接), 结束后恢复; 失败则整体回滚。
    conn.execute("PRAGMA ignore_check_constraints = ON")
    try:
        for object_type, object_id, field, _mv, confirmed_value in ops:
            table = TABLE_FOR_OBJECT[object_type]
            conn.execute(f"UPDATE {table} SET {field} = ?, updated_at = ? WHERE id = ?",
                         (json.dumps(confirmed_value, ensure_ascii=False)
                          if field in JSON_COLUMNS.get(table, set()) else confirmed_value,
                          ts, object_id))
        conn.execute("PRAGMA ignore_check_constraints = OFF")
        conn.commit()
    except Exception:
        conn.execute("PRAGMA ignore_check_constraints = OFF")
        conn.rollback()
        raise
    return op_id

def undo(conn, log_id: str, force: bool = False) -> str:
    """按操作号整体撤销 = 恢复该 op 全部字段的机器原值。日志本身不动（只增不改）。

    M3.1 守卫: 同一对象的同一字段若在此操作之后还有更新的操作,
    拒绝撤销（防止静默覆盖后续修改）, 除非 force=True 显式强制。
    """
    row = conn.execute("SELECT op_id FROM confirm_log WHERE id = ? OR op_id = ?",
                       (log_id, log_id)).fetchone()
    if row is None:
        raise ValueError(f"确认记录 {log_id} 不存在")
    op_id = row["op_id"]
    if not force:
        touched = conn.execute(
            "SELECT object_type, object_id, field, MAX(rowid) AS rid FROM confirm_log"
            " WHERE op_id = ? GROUP BY object_type, object_id, field", (op_id,)).fetchall()
        for f in touched:
            newer = conn.execute(
                "SELECT 1 FROM confirm_log WHERE object_type = ? AND object_id = ?"
                " AND field = ? AND rowid > ? LIMIT 1",
                (f["object_type"], f["object_id"], f["field"], f["rid"])).fetchone()
            if newer:
                raise ValueError(
                    f"同一字段在此操作后还有更新记录, 撤销会覆盖它; 如确认要回退请用 force:"
                    f" {f['object_type']}/{f['object_id'][:8]}/{f['field']}")
    conn.execute("PRAGMA ignore_check_constraints = ON")
    try:
        for r in conn.execute("SELECT * FROM confirm_log WHERE op_id = ? ORDER BY id", (op_id,)):
            table = TABLE_FOR_OBJECT[r["object_type"]]
            value = json.loads(r["machine_value"])
            conn.execute(f"UPDATE {table} SET {r['field']} = ?, updated_at = ? WHERE id = ?",
                         (json.dumps(value, ensure_ascii=False)
                          if r["field"] in JSON_COLUMNS.get(table, set()) else value,
                          _now(), r["object_id"]))
        conn.execute("PRAGMA ignore_check_constraints = OFF")
        conn.commit()
    except Exception:
        conn.execute("PRAGMA ignore_check_constraints = OFF")
        conn.rollback()
        raise
    return op_id


# ---------------------------------------------------------------- 文件不变量

def save_original(data_dir: Path, vehicle_id: str, asset_id: str, ext: str, data: bytes) -> Path:
    """写入原图；目标已存在即拒绝（原图不可变）。返回相对 data_dir 的路径。"""
    rel = f"assets/{vehicle_id}/originals/{asset_id}.{ext}"
    dest = Path(data_dir) / rel
    if dest.exists():
        raise FileExistsError(f"原图不可覆盖: {rel}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return str(rel)


def save_crop(data_dir: Path, vehicle_id: str, asset_id: str, ext: str, data: bytes) -> str:
    rel = f"assets/{vehicle_id}/crops/{asset_id}.{ext}"
    dest = Path(data_dir) / rel
    if dest.exists():
        raise FileExistsError(f"文件已存在: {rel}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return str(rel)


# ---------------------------------------------------------------- 派生查询（只查不存）

L1_VIEWS = ("hero_lf", "hero_rf", "side_l", "side_r", "hero_45", "side")
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
        " AND kind = 'crop' AND confirm_status != 'rejected'"
        " ORDER BY CASE confirm_status WHEN 'confirmed' THEN 0 ELSE 1 END",
        (vehicle_id, part_id)).fetchone()
    if row is None:
        return "缺失"
    if row["confirm_status"] == "confirmed" and row["binding_status"] == "confirmed":
        return "有·已确认"
    return "有·待确认"


def unbound_pool(conn) -> list[sqlite3.Row]:
    """待归号池 = binding_status='unbound' 且未被拒绝的素材（PRD FR-1.1 待确认分组）。"""
    return conn.execute(
        "SELECT * FROM assets WHERE binding_status = 'unbound' AND confirm_status != 'rejected'"
        " ORDER BY id").fetchall()


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
    row = conn.execute("SELECT vehicle_id, kind, view_angle, confirm_status FROM assets WHERE id = ?",
                       (asset_id,)).fetchone()
    if row is None:
        raise ValueError(f"素材 {asset_id} 不存在")
    if row["confirm_status"] == "rejected":
        raise ValueError("被拒素材不得设为主图")
    if row["vehicle_id"] != vehicle_id or row["view_angle"] not in ("hero_lf", "hero_rf"):
        raise ValueError("主图必须是该车已对号的 3/4 主视角素材")
    conn.execute("UPDATE vehicles SET hero_asset_id = ? WHERE id = ?", (asset_id, vehicle_id))
    conn.commit()
