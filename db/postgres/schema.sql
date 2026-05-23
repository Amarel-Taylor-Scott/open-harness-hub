-- ----------------------------------------------------------------------------
-- Open Harness Hub — canonical PostgreSQL schema (v0.1.0)
--
-- Maps one row per artifact, with JSONB body for type-specific fields and
-- small join tables for the array-valued cross-cutting axes (industry,
-- capability, modality, tag). Rule and knowledge leaves get their own
-- query-friendly tables.
--
-- This schema is the SOURCE OF TRUTH for relational stores. Document /
-- key-value / vector mappings derive from this.
-- ----------------------------------------------------------------------------

BEGIN;

-- The artifact table holds one row per published manifest.
CREATE TABLE IF NOT EXISTS artifact (
  id              TEXT PRIMARY KEY,
  type            TEXT NOT NULL
                       CHECK (type IN ('harness','pipeline','benchmark','rule-pack','knowledge-pack','logic-pack','tool','persona','adapter','rubric','dataset','schema')),
  version         TEXT NOT NULL,
  name            TEXT NOT NULL,
  description     TEXT NOT NULL,
  license         TEXT NOT NULL,
  lifecycle       TEXT NOT NULL
                       CHECK (lifecycle IN ('experimental','beta','stable','deprecated')),
  trust_boundary  TEXT
                       CHECK (trust_boundary IS NULL OR trust_boundary IN ('local','hub','external','mixed')),
  freshness       TEXT
                       CHECK (freshness IS NULL OR freshness IN ('stable','volatile','dated')),
  created         DATE,
  updated         DATE,
  superseded_by   TEXT REFERENCES artifact(id),
  deprecated_on   DATE,
  attribution     JSONB,
  links           JSONB,
  body            JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS artifact_type_idx     ON artifact (type);
CREATE INDEX IF NOT EXISTS artifact_lifecycle_idx ON artifact (lifecycle);

-- One row per (artifact, industry) — supports filter by industry.
CREATE TABLE IF NOT EXISTS artifact_industry (
  artifact_id TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  industry    TEXT NOT NULL,
  PRIMARY KEY (artifact_id, industry)
);
CREATE INDEX IF NOT EXISTS artifact_industry_industry_idx ON artifact_industry (industry);

CREATE TABLE IF NOT EXISTS artifact_capability (
  artifact_id TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  capability  TEXT NOT NULL,
  PRIMARY KEY (artifact_id, capability)
);
CREATE INDEX IF NOT EXISTS artifact_capability_capability_idx ON artifact_capability (capability);

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

-- Inter-artifact edges — consumes / emits / step_ref / contributes_to / etc.
CREATE TABLE IF NOT EXISTS artifact_ref (
  src_id TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  dst_id TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  role   TEXT NOT NULL,
  PRIMARY KEY (src_id, dst_id, role)
);
CREATE INDEX IF NOT EXISTS artifact_ref_dst_idx ON artifact_ref (dst_id, role);

-- Rule leaves (inside rule packs). One row per rule.
CREATE TABLE IF NOT EXISTS rule (
  rule_id    TEXT PRIMARY KEY,
  pack_id    TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  family     TEXT NOT NULL
                  CHECK (family IN ('grep','glob','classifier','heuristic','rag','citation','online_search','privacy','schema','routing')),
  severity   TEXT,
  category   TEXT,
  pattern    TEXT,
  body       JSONB NOT NULL,
  enabled    BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS rule_pack_idx ON rule (pack_id);
CREATE INDEX IF NOT EXISTS rule_family_idx ON rule (family);
CREATE INDEX IF NOT EXISTS rule_category_idx ON rule (category);
CREATE INDEX IF NOT EXISTS rule_severity_idx ON rule (severity);

-- Knowledge leaves (inside knowledge / logic packs). One row per leaf.
CREATE TABLE IF NOT EXISTS knowledge_leaf (
  leaf_id    TEXT PRIMARY KEY,
  pack_id    TEXT NOT NULL REFERENCES artifact(id) ON DELETE CASCADE,
  leaf_type  TEXT NOT NULL,
  industry   TEXT,
  language   TEXT,
  body       JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS knowledge_leaf_pack_idx     ON knowledge_leaf (pack_id);
CREATE INDEX IF NOT EXISTS knowledge_leaf_type_idx     ON knowledge_leaf (leaf_type);
CREATE INDEX IF NOT EXISTS knowledge_leaf_industry_idx ON knowledge_leaf (industry);

-- A pipeline / benchmark / harness run. Append-only.
CREATE TABLE IF NOT EXISTS run (
  run_id      TEXT PRIMARY KEY,
  artifact_id TEXT NOT NULL REFERENCES artifact(id),
  started_at  TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ,
  status      TEXT NOT NULL CHECK (status IN ('queued','running','succeeded','failed','cancelled')),
  adapter_id  TEXT REFERENCES artifact(id),
  inputs      JSONB,
  outputs     JSONB,
  trace       JSONB,
  cost_usd    NUMERIC,
  trust_boundary TEXT
);
CREATE INDEX IF NOT EXISTS run_artifact_started_idx ON run (artifact_id, started_at DESC);

COMMIT;
