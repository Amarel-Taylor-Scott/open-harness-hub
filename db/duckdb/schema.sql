-- ----------------------------------------------------------------------------
-- OpenHubForAI — DuckDB schema (v0.1.0)
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

CREATE TABLE IF NOT EXISTS component (
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

CREATE INDEX IF NOT EXISTS component_type_idx ON component (type);

CREATE TABLE IF NOT EXISTS component_ref (
  src_id VARCHAR NOT NULL REFERENCES component(id),
  dst_id VARCHAR NOT NULL REFERENCES component(id),
  role   VARCHAR NOT NULL,
  PRIMARY KEY (src_id, dst_id, role)
);

CREATE TABLE IF NOT EXISTS rule (
  rule_id   VARCHAR PRIMARY KEY,
  pack_id   VARCHAR NOT NULL REFERENCES component(id),
  family    VARCHAR NOT NULL,
  severity  VARCHAR,
  category  VARCHAR,
  pattern   VARCHAR,
  body      JSON NOT NULL,
  enabled   BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS knowledge_leaf (
  leaf_id   VARCHAR PRIMARY KEY,
  pack_id   VARCHAR NOT NULL REFERENCES component(id),
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
  component_id   VARCHAR NOT NULL REFERENCES component(id),
  started_at    TIMESTAMPTZ NOT NULL,
  finished_at   TIMESTAMPTZ,
  status        VARCHAR NOT NULL,
  adapter_id    VARCHAR REFERENCES component(id),
  inputs        JSON,
  outputs       JSON,
  trace         JSON,
  cost_usd      DOUBLE,
  trust_boundary VARCHAR
);

-- Build FTS index over components.
PRAGMA create_fts_index('component', 'id', 'name', 'description', overwrite=1);

-- Sample analytical queries:
--   SELECT type, count(*) FROM component GROUP BY type;
--   SELECT * FROM component WHERE 'healthcare.clinical' IN industry;
--   SELECT * FROM knowledge_leaf
--     ORDER BY array_distance(embedding, :query_vector)
--     LIMIT 10;
