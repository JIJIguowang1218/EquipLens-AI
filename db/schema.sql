-- EquipLens 数据层 DDL v0.1
-- 规范: docs/data-model-spec.md | 不变量由 CHECK / 触发器在此强制
PRAGMA foreign_keys = ON;

CREATE TABLE vocab (
  id     TEXT PRIMARY KEY,
  type   TEXT NOT NULL CHECK (type IN ('part')),
  term   TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','retired')),
  note   TEXT,
  UNIQUE (type, term)
);

CREATE TABLE vehicles (
  id            TEXT PRIMARY KEY,
  brand         TEXT NOT NULL,
  model_name    TEXT NOT NULL,
  category      TEXT,
  generation    TEXT,
  list_status   TEXT NOT NULL DEFAULT 'candidate' CHECK (list_status IN ('candidate','locked')),
  hero_asset_id TEXT,                          -- 逻辑指针, 访问层 set_hero() 校验
  project_id    TEXT,                          -- 预留
  created_at    TEXT NOT NULL,
  UNIQUE (brand, model_name, generation)
);

CREATE TABLE assets (
  id               TEXT PRIMARY KEY,
  vehicle_id       TEXT REFERENCES vehicles(id),
  binding_status   TEXT NOT NULL CHECK (binding_status IN ('unbound','provisional','confirmed')),
  binding_evidence TEXT NOT NULL CHECK (binding_evidence IN ('none','self_derived','region_match','co_occurrence_labeled','co_occurrence_only','human')),
  kind             TEXT NOT NULL CHECK (kind IN ('source_image','crop')),
  parent_asset_id  TEXT REFERENCES assets(id),
  crop_bbox        TEXT,                       -- JSON {"x","y","w","h"}
  file_path        TEXT NOT NULL,
  view_angle       TEXT NOT NULL CHECK (view_angle IN ('hero_lf','hero_rf','front','rear','side_l','side_r','ortho_sheet','detail','interior','scene','nameplate')),
  asset_nature     TEXT NOT NULL CHECK (asset_nature IN ('render','official_photo','real_photo','report_screenshot')),
  part_id          TEXT REFERENCES vocab(id),
  width            INTEGER,
  height           INTEGER,
  quality_flags    TEXT,                       -- JSON array
  hash_sha256      TEXT NOT NULL CHECK (length(hash_sha256) = 64),
  phash            TEXT CHECK (phash IS NULL OR length(phash) = 16),
  confirm_status   TEXT NOT NULL CHECK (confirm_status IN ('machine_tagged','confirmed','rejected')),
  notes            TEXT,
  created_at       TEXT NOT NULL,
  updated_at       TEXT NOT NULL,
  -- 不变量: 裁图必有父图与bbox, 原图必无
  CHECK ((kind = 'crop') = (parent_asset_id IS NOT NULL AND crop_bbox IS NOT NULL)),
  -- 不变量: unbound 与 vehicle_id 互斥联动
  CHECK ((vehicle_id IS NULL) = (binding_status = 'unbound')),
  CHECK ((binding_evidence = 'none') = (binding_status = 'unbound'))
);

CREATE TABLE sources (
  id           TEXT PRIMARY KEY,
  asset_id     TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  url          TEXT,
  platform     TEXT,
  retrieved_at TEXT,
  license      TEXT NOT NULL CHECK (license IN ('client_provided','self_captured','web_official','web_third_party')),
  is_primary   INTEGER NOT NULL CHECK (is_primary IN (0,1)),
  note         TEXT
);

CREATE TABLE facts (
  id             TEXT PRIMARY KEY,
  vehicle_id     TEXT NOT NULL REFERENCES vehicles(id),
  field_key      TEXT NOT NULL,
  value          TEXT NOT NULL,
  unit           TEXT,
  source_id      TEXT REFERENCES sources(id),
  confirm_status TEXT NOT NULL CHECK (confirm_status IN ('machine_tagged','confirmed','rejected')),
  created_at     TEXT NOT NULL,
  updated_at     TEXT NOT NULL
);

CREATE TABLE descriptions (
  id                 TEXT PRIMARY KEY,
  vehicle_id         TEXT NOT NULL REFERENCES vehicles(id),
  node_type          TEXT NOT NULL CHECK (node_type IN ('whole','part')),
  part_id            TEXT REFERENCES vocab(id),
  axis_type          TEXT NOT NULL CHECK (axis_type IN ('structure','design_feature','intent')),
  scope              TEXT NOT NULL CHECK (scope IN ('family','model')),
  body               TEXT NOT NULL CHECK (length(body) >= 1),
  evidence_asset_ids TEXT NOT NULL,            -- JSON array, >=1 (schema 层强制)
  source_ids         TEXT,                     -- JSON array
  confirm_status     TEXT NOT NULL CHECK (confirm_status IN ('machine_tagged','confirmed','rejected')),
  version            INTEGER NOT NULL DEFAULT 1,
  created_at         TEXT NOT NULL,
  updated_at         TEXT NOT NULL,
  CHECK ((node_type = 'part') = (part_id IS NOT NULL))
);

CREATE TABLE confirm_log (
  id              TEXT PRIMARY KEY,
  op_id           TEXT NOT NULL,
  object_type     TEXT NOT NULL CHECK (object_type IN ('vehicle','asset','source','fact','description')),
  object_id       TEXT NOT NULL,
  field           TEXT NOT NULL,
  machine_value   TEXT NOT NULL,               -- JSON 文本, 撤销依据
  confirmed_value TEXT NOT NULL,               -- JSON 文本
  method          TEXT NOT NULL CHECK (method IN ('single','batch','auto')),
  confirmed_at    TEXT NOT NULL,
  confirmed_by    TEXT NOT NULL DEFAULT 'user'
);

-- 不变量: confirm_log 只增不改 (触发器强制)
CREATE TRIGGER confirm_log_no_update BEFORE UPDATE ON confirm_log
BEGIN SELECT RAISE(ABORT, 'confirm_log is append-only'); END;
CREATE TRIGGER confirm_log_no_delete BEFORE DELETE ON confirm_log
BEGIN SELECT RAISE(ABORT, 'confirm_log is append-only'); END;

CREATE INDEX idx_assets_vehicle   ON assets(vehicle_id);
CREATE INDEX idx_assets_parent    ON assets(parent_asset_id);
CREATE INDEX idx_sources_asset    ON sources(asset_id);
CREATE INDEX idx_facts_vehicle    ON facts(vehicle_id);
CREATE INDEX idx_desc_vehicle     ON descriptions(vehicle_id);
CREATE INDEX idx_log_object       ON confirm_log(object_type, object_id);
