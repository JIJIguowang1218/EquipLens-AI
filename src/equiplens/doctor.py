"""M3.1 数据完整性巡检（fsck）：只报告，不修复。修复走既有工作流命令。

巡检项: 缺失文件 / 孤儿文件 / 悬空主图指针 / 悬空父子引用 / 残留变体组。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def doctor(conn: sqlite3.Connection, data_dir: Path) -> dict:
    data_dir = Path(data_dir)
    issues: dict[str, list] = {"missing_files": [], "orphan_files": [], "dangling_hero": [],
                               "dangling_parent": [], "dangling_vehicle": [],
                               "stale_variant_groups": []}

    # 文件 <-> 数据库 双向核对
    db_files: set[str] = set()
    for r in conn.execute("SELECT id, file_path FROM assets"):
        p = data_dir / r["file_path"]
        if p.is_file():
            db_files.add(str(p).lower())
        else:
            issues["missing_files"].append({"asset_id": r["id"], "file_path": r["file_path"]})
    assets_root = data_dir / "assets"
    disk_files = ({str(p).lower() for p in assets_root.rglob("*") if p.is_file()}
                  if assets_root.exists() else set())
    issues["orphan_files"] = sorted(disk_files - db_files)

    # 主图指针有效性: 存在 / 未被拒 / 已对号 / 归属该车
    for r in conn.execute(
            """SELECT v.id AS vid, v.hero_asset_id, a.id AS aid, a.confirm_status,
                      a.binding_status, a.vehicle_id
               FROM vehicles v LEFT JOIN assets a ON a.id = v.hero_asset_id"""):
        if r["hero_asset_id"] is None:
            continue
        if (r["aid"] is None or r["confirm_status"] == "rejected"
                or r["binding_status"] != "confirmed" or r["vehicle_id"] != r["vid"]):
            issues["dangling_hero"].append({"vehicle_id": r["vid"],
                                            "hero_asset_id": r["hero_asset_id"]})

    # 父图 / 车型引用悬空（正常被外键拦住, 巡检兜底防御绕过契约的写入）
    for r in conn.execute("SELECT id, parent_asset_id FROM assets WHERE parent_asset_id IS NOT NULL"):
        if conn.execute("SELECT 1 FROM assets WHERE id = ?",
                        (r["parent_asset_id"],)).fetchone() is None:
            issues["dangling_parent"].append({"asset_id": r["id"],
                                              "parent_asset_id": r["parent_asset_id"]})
    for r in conn.execute("SELECT id, vehicle_id FROM assets WHERE vehicle_id IS NOT NULL"):
        if conn.execute("SELECT 1 FROM vehicles WHERE id = ?",
                        (r["vehicle_id"],)).fetchone() is None:
            issues["dangling_vehicle"].append({"asset_id": r["id"], "vehicle_id": r["vehicle_id"]})

    # 残留变体组: 有效成员 < 2 的组
    for r in conn.execute(
            """SELECT variant_group AS g, count(*) AS c FROM assets
               WHERE variant_group IS NOT NULL AND confirm_status != 'rejected'
               GROUP BY variant_group HAVING c < 2"""):
        issues["stale_variant_groups"].append({"group": r["g"], "members": r["c"]})

    total = sum(len(v) for v in issues.values())
    return {"ok": total == 0, "total_issues": total, "issues": issues}
