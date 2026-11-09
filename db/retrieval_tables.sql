-- 检索中证据表（P0 契约，P2 才接入读写）
-- 与 docs/retrieval-build-plan-20261109.md 的 P0/P2 对应；不修改现有 equip 表。

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
    identity_status TEXT,              -- confirmed | probable | unknown
    origin_status   TEXT,              -- oem | modified | unknown
    visibility      TEXT,              -- full | partial | not_visible
    evidence_grade  TEXT,              -- E1 | E2 | E3
    evidence_score  REAL,
    source_url      TEXT,
    verified_by     TEXT,
    verified_at     TEXT,
    UNIQUE (run_id, asset_id, part)
);

CREATE TABLE IF NOT EXISTS asset_part_feasibility (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        TEXT NOT NULL,
    part            TEXT NOT NULL,
    state           TEXT NOT NULL,     -- visible | not_visible | unknown
    method          TEXT,              -- analysis | metadata | model | human
    confidence      REAL,
    checked_at      TEXT,
    UNIQUE (asset_id, part)
);
