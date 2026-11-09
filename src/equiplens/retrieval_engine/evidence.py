"""证据落库：把引擎的 evidence rows 写进 image_evidence（P2-W1）。"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS image_evidence (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL,
    asset_id        TEXT NOT NULL,
    vehicle_id      TEXT,
    model           TEXT,
    part            TEXT NOT NULL,
    location        TEXT,
    view            TEXT,
    width           INTEGER,
    height          INTEGER,
    identity_status TEXT,
    origin_status   TEXT,
    visibility      TEXT,
    evidence_grade  TEXT,
    evidence_score  REAL,
    source_url      TEXT,
    verified_by     TEXT,
    verified_at     TEXT,
    UNIQUE (run_id, asset_id, part)
);
"""


class EvidenceStore:
    def __init__(self, db_path: str | Path):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def write_rows(self, run_id: str, rows: list[dict],
                   verified_by: str = "rule-v1") -> int:
        if not rows:
            return 0
        with closing(sqlite3.connect(self.path)) as conn:
            conn.executemany(
                """INSERT OR REPLACE INTO image_evidence
                   (run_id, asset_id, vehicle_id, model, part, location, view,
                    width, height, identity_status, origin_status, visibility,
                    evidence_grade, evidence_score, source_url, verified_by, verified_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                [
                    (run_id, r.get("asset_id"), r.get("vehicle_id"),
                     r.get("model"), r.get("part"), r.get("location"),
                     r.get("view"), r.get("width"), r.get("height"),
                     r.get("identity"), r.get("origin"), r.get("visibility"),
                     r.get("grade"), r.get("evidence_score"),
                     r.get("source_url"), verified_by)
                    for r in rows
                ])
            conn.commit()
        return len(rows)

    def count(self) -> int:
        with closing(sqlite3.connect(self.path)) as conn:
            return int(conn.execute("SELECT COUNT(*) FROM image_evidence")
                       .fetchone()[0])
