-- ----------------------------------------------------------------------------
-- Open Harness Hub — DuckDB schema (v0.1.0)
--
-- DuckDB is an embedded analytical (OLAP) database with native JSON,
-- LIST/STRUCT types, columnar storage, and a vector-search extension
-- (vss). Excellent for catalog analytics and ad-hoc queries over JSONL
-- run logs without standing up a server.
-- ----------------------------------------------------------------------------

INSTALL json;       LOAD json;
INSTALL fts;        LOAD fts;
INSTALL vss;        LOAD vss;

CREATE SEQUENCE IF NOT EXISTS run_seq START 1;

CREATE TABLE IF NOT EXISTS artifact (
  id              VARCHAR PRIMARY KEY,
  type            VARCHAR NOT NULL,
  version         VARCHAR NOT NULL,
  name            VARCHAR NOT NULL,
  description     VARCHAR NOT NULL,
  license         VARCHAR NOT NULL,
  lifecycle       VARCHAR NOT NULL,
  trust_boundary  VARCHAR,
  freshness       VARCHAR,
  created         DATE,
  updated         DATE,
  industry        VARCHAR[],                    -- native list
  capability      VARCHAR[],
  modality        VARCHAR[],
  tags            VARCHAR[],
  attribution     JSON,
  links           JSON,
  body            JSON NOT NULL
);

CREATE INDEX IF NOT EXISTS artifact_type_idx ON artifact (type);

CREATE TABLE IF NOT EXISTS artifact_ref (
  src_id VARCHAR NOT NULL REFERENCES artifact(id),
  dst_id VARCHAR NOT NULL REFERENCES artifact(id),
  role   VARCHAR NOT NULL,
  PRIMARY KEY (src_id, dst_id, role)
);

CREATE TABLE IF NOT EXISTS rule (
  rule_id   VARCHAR PRIMARY KEY,
  pack_id   VARCHAR NOT NULL REFERENCES artifact(id),
  family    VARCHAR NOT NULL,
  severity  VARCHAR,
  category  VARCHAR,
  pattern   VARCHAR,
  body      JSON NOT NULL,
  enabled   BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS knowledge_leaf (
  leaf_id   VARCHAR PRIMARY KEY,
  pack_id   VARCHAR NOT NULL REFERENCES artifact(id),
  leaf_type VARCHAR NOT NULL,
  industry  VARCHAR,
  language  VARCHAR,
  body      JSON NOT NULL,
  embedding FLOAT[384]                         -- native, used by vss extension
);

CREATE INDEX IF NOT EXISTS knowledge_leaf_emb_idx
  ON knowledge_leaf USING HNSW (embedding) WITH (metric = 'cosine');

CREATE TABLE IF NOT EXISTS run (
  run_id        VARCHAR PRIMARY KEY DEFAULT ('run_' || nextval('run_seq')),
  artifact_id   VARCHAR NOT NULL REFERENCES artifact(id),
  started_at    TIMESTAMPTZ NOT NULL,
  finished_at   TIMESTAMPTZ,
  status        VARCHAR NOT NULL,
  adapter_id    VARCHAR REFERENCES artifact(id),
  inputs        JSON,
  outputs       JSON,
  trace         JSON,
  cost_usd      DOUBLE,
  trust_boundary VARCHAR
);

-- Build FTS index over artifacts.
PRAGMA create_fts_index('artifact', 'id', 'name', 'description', overwrite=1);

-- Sample analytical queries:
--   SELECT type, count(*) FROM artifact GROUP BY type;
--   SELECT * FROM artifact WHERE 'healthcare.clinical' IN industry;
--   SELECT * FROM knowledge_leaf
--     ORDER BY array_distance(embedding, :query_vector)
--     LIMIT 10;
