"""M3 库内检索：组合过滤 / 同尺寸聚类 / 相似检索 / 文字搜索 / 词表服务（含提名池）。

被检索模块与分析模块共用。只读为主；词表生命周期操作走 confirm 落账。
"""

from __future__ import annotations

import uuid

from . import db


# ---------------------------------------------------------------- 组合过滤

def query_assets(conn, *, vehicle_id: str | None = None, view: str | None = None,
                 kind: str | None = None, part_id: str | None = None,
                 license: str | None = None, quality_flag: str | None = None,
                 confirm_status: str | None = None, binding_status: str | None = None,
                 include_rejected: bool = False) -> list:
    """结构化标签组合过滤——"检索标签"的统一入口。默认排除被拒素材。"""
    sql = ["SELECT a.* FROM assets a WHERE 1=1"]
    params: list = []
    if not include_rejected:
        sql.append(" AND a.confirm_status != 'rejected'")
    if vehicle_id:
        sql.append(" AND a.vehicle_id = ?"); params.append(vehicle_id)
    if view:
        sql.append(" AND a.view_angle = ?"); params.append(view)
    if kind:
        sql.append(" AND a.kind = ?"); params.append(kind)
    if part_id:
        sql.append(" AND a.part_id = ?"); params.append(part_id)
    if confirm_status:
        sql.append(" AND a.confirm_status = ?"); params.append(confirm_status)
    if binding_status:
        sql.append(" AND a.binding_status = ?"); params.append(binding_status)
    if license:
        sql.append(" AND EXISTS (SELECT 1 FROM sources s WHERE s.asset_id = a.id AND s.license = ?)")
        params.append(license)
    if quality_flag:
        sql.append(" AND a.quality_flags LIKE ?"); params.append(f'%"{quality_flag}"%')
    sql.append(" ORDER BY a.vehicle_id, a.file_path")
    return conn.execute(" ".join(sql), params).fetchall()


def same_dimension_clusters(conn, min_group: int = 2) -> list[list]:
    """同尺寸素材聚类——"疑似同图变体"的人工比对候选（不含被拒素材）。"""
    rows = conn.execute(
        "SELECT a.* FROM assets a WHERE a.width IS NOT NULL AND a.confirm_status != 'rejected'"
        " ORDER BY a.width, a.height, a.id").fetchall()
    groups: dict[tuple, list] = {}
    for r in rows:
        groups.setdefault((r["width"], r["height"]), []).append(r)
    return [g for g in groups.values() if len(g) >= min_group]


def find_similar(conn, asset_id: str, max_dist: int = 8) -> list[tuple]:
    """感知哈希相似检索: 与指定素材 dHash 距离 <= max_dist 的其他素材, 按距离升序。"""
    me = conn.execute("SELECT phash FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if me is None:
        raise ValueError(f"素材 {asset_id} 不存在")
    if not me["phash"]:
        raise ValueError(f"素材 {asset_id} 无感知哈希")
    out = []
    for r in conn.execute("SELECT * FROM assets WHERE phash IS NOT NULL AND id != ? AND confirm_status != 'rejected'",
                          (asset_id,)):
        dist = ingest_hamming(me["phash"], r["phash"])
        if dist <= max_dist:
            out.append((r, dist))
    return sorted(out, key=lambda t: t[1])


def ingest_hamming(hex_a: str, hex_b: str) -> int:
    return bin(int(hex_a, 16) ^ int(hex_b, 16)).count("1")


def text_search(conn, text: str, include_rejected: bool = False) -> list:
    """全局文字搜索: 型号/品牌/年款/备注/文件路径/来源平台/URL/来源备注。"""
    p = f"%{text}%"
    sql = """SELECT DISTINCT a.* FROM assets a
             LEFT JOIN vehicles v ON v.id = a.vehicle_id
             WHERE (:rej = 1 OR a.confirm_status != 'rejected')
               AND (a.notes LIKE :p OR a.file_path LIKE :p
                    OR v.brand LIKE :p OR v.model_name LIKE :p OR v.generation LIKE :p
                    OR EXISTS (SELECT 1 FROM sources s WHERE s.asset_id = a.id
                               AND (s.platform LIKE :p OR s.url LIKE :p OR s.note LIKE :p)))
             ORDER BY a.vehicle_id, a.file_path"""
    return conn.execute(sql, {"rej": 1 if include_rejected else 0, "p": p}).fetchall()


# ---------------------------------------------------------------- 词表服务（提名池）

def vocab_list(conn, include_pending: bool = False, include_retired: bool = False) -> list:
    """默认只列正式词表(active); 提名池(pending)与退役(retired)按需展开。"""
    states = ["active"]
    if include_pending:
        states.append("pending")
    if include_retired:
        states.append("retired")
    marks = ",".join("?" for _ in states)
    return conn.execute(
        f"SELECT * FROM vocab WHERE status IN ({marks}) ORDER BY type, term", states).fetchall()


def vocab_add(conn, term: str, note: str | None = None, term_id: str | None = None) -> str:
    """自由标签入口: 进提名池(pending), 可用可搜但标记未受控; 人工提升后转正。"""
    tid = term_id or term  # 默认以词本身作 ID, 可读且唯一约束兜底
    conn.execute("INSERT INTO vocab (id, type, term, status, note) VALUES (?, 'part', ?, 'pending', ?)",
                 (tid, term, note))
    conn.commit()
    return tid


def vocab_promote(conn, term_id: str) -> str:
    row = conn.execute("SELECT status FROM vocab WHERE id = ?", (term_id,)).fetchone()
    if row is None:
        raise ValueError(f"词表项 {term_id} 不存在")
    return db.confirm(conn, "vocab", term_id, "status",
                      row["status"], "active", method="single", op_id=f"op-{uuid.uuid4().hex[:12]}")


def vocab_retire(conn, term_id: str) -> str:
    row = conn.execute("SELECT status FROM vocab WHERE id = ?", (term_id,)).fetchone()
    if row is None:
        raise ValueError(f"词表项 {term_id} 不存在")
    return db.confirm(conn, "vocab", term_id, "status",
                      row["status"], "retired", method="single", op_id=f"op-{uuid.uuid4().hex[:12]}")
