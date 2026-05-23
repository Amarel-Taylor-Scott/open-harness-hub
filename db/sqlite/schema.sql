-- ----------------------------------------------------------------------------
-- Open Harness Hub — SQLite schema (v0.1.0)
--
-- Same row model as PostgreSQL but with SQLite-compatible types
-- (no JSONB → use JSON text; no CHECK on FK; no DOMAIN).
-- ----------------------------------------------------------------------------

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS artifact (
  id              TEXT PRIMARY KEY,
  type            TEXT NOT NULL CHECK (type IN ('harness','pipeline','benchmark','rule-pack','knowledge-pack','logic-pack','tool','persona','adapter','rubric','dataset','schema','processor')),
  version         TEXT NOT NULL,
  name            TEXT NOT NULL,
  description     TEXT NOT NULL,
  license         TEXT NOT NULL,
  lifecycle       TEXT NOT NULL CHECK (lifecycle IN ('experimental','beta','stable','deprecated')),
  trust_boundary  TEXT,
  freshness       TEXT,
  created         TEXT,                       -- ISO date as TEXT (SQLite lacks DATE type)
  updated         TEXT,
  superseded_by   TEXT REFERENCES artifact(id),
  deprecated_on   TEXT,
  attribution     TEXT,                       -- JSON text
  links           TEXT,                       -- JSON text
  body            TEXT NOT NULL               -- full manifest as JSON text
);

CREATE INDEX IF NOT EXISTS artifact_type_idx       ON artifact (type);
CREATE INDEX IF NOT EXISTS artifact_lifecycle_idx  ON artifact (lifecycle);

CREATE TABLE IF NOT EXISTS artifact_industry (
  artifact_id TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  industry    TEXT NOT NULL,
  PRIMARY KEY (artifact_id, industry)
);

CREATE TABLE IF NOT EXISTS artifact_capability (
  artifact_id TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  capability  TEXT NOT NULL,
  PRIMARY KEY (artifact_id, capability)
);

CREATE TABLE IF NOT EXISTS artifact_modality (
  artifact_id TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  modality    TEXT NOT NULL,
  PRIMARY KEY (artifact_id, modality)
);

CREATE TABLE IF NOT EXISTS artifact_tag (
  artifact_id TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  tag         TEXT NOT NULL,
  PRIMARY KEY (artifact_id, tag)
);

CREATE TABLE IF NOT EXISTS artifact_ref (
  src_id TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  dst_id TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  role   TEXT NOT NULL,
  PRIMARY KEY (src_id, dst_id, role)
);

CREATE TABLE IF NOT EXISTS rule (
  rule_id    TEXT PRIMARY KEY,
  pack_id    TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  family     TEXT NOT NULL,
  severity   TEXT,
  category   TEXT,
  pattern    TEXT,
  body       TEXT NOT NULL,
  enabled    INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS rule_pack_idx     ON rule (pack_id);
CREATE INDEX IF NOT EXISTS rule_family_idx   ON rule (family);
CREATE INDEX IF NOT EXISTS rule_severity_idx ON rule (severity);

CREATE TABLE IF NOT EXISTS knowledge_leaf (
  leaf_id    TEXT PRIMARY KEY,
  pack_id    TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  leaf_type  TEXT NOT NULL,
  industry   TEXT,
  language   TEXT,
  body       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS knowledge_leaf_pack_idx ON knowledge_leaf (pack_id);
CREATE INDEX IF NOT EXISTS knowledge_leaf_type_idx ON knowledge_leaf (leaf_type);

CREATE TABLE IF NOT EXISTS run (
  run_id      TEXT PRIMARY KEY,
  artifact_id TEXT NOT NULL REFERENCES artifact(id),
  started_at  TEXT NOT NULL,
  finished_at TEXT,
  status      TEXT NOT NULL CHECK (status IN ('queued','running','succeeded','failed','cancelled')),
  adapter_id  TEXT REFERENCES artifact(id),
  inputs      TEXT,
  outputs     TEXT,
  trace       TEXT,
  cost_usd    REAL,
  trust_boundary TEXT
);
CREATE INDEX IF NOT EXISTS run_artifact_started_idx ON run (artifact_id, started_at DESC);

-- FTS5 full-text search over artifact name+description+tags
-- (run after the artifact table is populated).
CREATE VIRTUAL TABLE IF NOT EXISTS artifact_fts USING fts5(
  id UNINDEXED,
  name,
  description,
  tags,
  content='',
  tokenize='porter unicode61'
);
