# -*- coding: utf-8 -*-
"""库内素材盘点：某车型有没有可用的主图候选（只查库，不联网）。

只回答一件事："不用爬，这个车型库里有几张能当主图的图？"——判的是
单台/视角/分辨率这些可计算项；"能不能裁出请求部件"仍标 to_verify。

用法:
    python inventory.py --models 德龙6X6,H6066 --db data-test/equiplens.db
    python inventory.py --models-file models.txt --min-width 1200 --out inv.json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

HERO_VIEWS = ("hero_45", "hero_lf", "hero_rf", "side", "side_l", "side_r", "front")


def _connect(db: Path) -> tuple[sqlite3.Connection | None, str]:
    if not db.exists():
        return None, "db_missing"
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        conn.execute("SELECT count(*) FROM assets").fetchone()
        return conn, "ok"
    except sqlite3.Error:
        return None, "db_unreadable"


def inventory(db: Path, models: list[str], min_width: int = 1200) -> dict:
    conn, status = _connect(db)
    out = {"db": str(db), "library_status": status, "min_width": min_width,
           "models": [], "warnings": []}
    if conn is None:
        out["warnings"].append(f"库不可用({status})：所有车型标记 to_verify，不得当已有素材")
        for m in models:
            out["models"].append({"query": m, "matched": [], "hero_candidates": 0,
                                  "to_verify": True})
        return out

    try:
        total_assets = conn.execute("SELECT count(*) FROM assets").fetchone()[0]
        out["total_assets"] = total_assets
        if not total_assets:
            out["warnings"].append("库为空（0 条素材）：不得据此判断'没有素材'，只能标 to_verify")

        for m in models:
            rows = conn.execute(
                "SELECT id, brand, model_name FROM vehicles "
                "WHERE model_name LIKE ? OR (brand || model_name) LIKE ?",
                (f"%{m}%", f"%{m}%")).fetchall()
            ids = [r[0] for r in rows]
            heroes = 0
            if ids:
                q = ("SELECT count(*) FROM assets WHERE kind='source_image' "
                     "AND confirm_status != 'rejected' AND vehicle_id IN ({}) "
                     "AND view_angle IN ({}) AND (width IS NULL OR width >= ?)"
                     ).format(",".join("?" * len(ids)),
                              ",".join("?" * len(HERO_VIEWS)))
                heroes = conn.execute(q, (*ids, *HERO_VIEWS, min_width)).fetchone()[0]
            out["models"].append({
                "query": m,
                "matched": [{"id": r[0], "brand": r[1], "model": r[2]} for r in rows],
                "hero_candidates": heroes,
                "has_usable_hero": heroes > 0,
                "to_verify": heroes == 0,
                "parts_croppable": "to_verify",
            })
    finally:
        conn.close()
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="库内主图盘点（只读）")
    ap.add_argument("--db", default="data-test/equiplens.db")
    ap.add_argument("--models", help="逗号分隔的车型名")
    ap.add_argument("--models-file", help="每行一个车型名")
    ap.add_argument("--min-width", type=int, default=1200)
    ap.add_argument("--out", help="写出 JSON（默认打印）")
    a = ap.parse_args(argv)
    models: list[str] = []
    if a.models:
        models += [x.strip() for x in a.models.split(",") if x.strip()]
    if a.models_file:
        models += [x.strip() for x in Path(a.models_file).read_text(encoding="utf-8").splitlines()
                   if x.strip()]
    if not models:
        print(json.dumps({"ok": False, "error": "未给 --models/--models-file"},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    res = inventory(Path(a.db), models, a.min_width)
    text = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"→ {a.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
