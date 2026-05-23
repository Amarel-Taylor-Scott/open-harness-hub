-- ----------------------------------------------------------------------------
-- Open Harness Hub — BigQuery schema (v0.1.0)
--
-- BigQuery shape uses native ARRAY + STRUCT (no join tables needed for
-- industry/capability/modality/tags). Suitable for warehouse-scale
-- analytics over run logs and catalog evolution.
-- ----------------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS open_harness_hub;

CREATE TABLE IF NOT EXISTS open_harness_hub.artifact (
  id              STRING NOT NULL,
  type            STRING NOT NULL,
  version         STRING NOT NULL,
  name            STRING NOT NULL,
  description     STRING NOT NULL,
  license         STRING NOT NULL,
  lifecycle       STRING NOT NULL,
  lifecycle_position STRING,
  trust_boundary  STRING,
  freshness       STRING,
  industry        ARRAY<STRING>,
  capability      ARRAY<STRING>,
  modality        ARRAY<STRING>,
  tags            ARRAY<STRING>,
  created         DATE,
  updated         DATE,
  eu_ai_act_risk  STRING,
  attribution     STRUCT<
    source_url  STRING,
    source_kind STRING,
    author      STRING,
    license     STRING
  >,
  body            JSON NOT NULL,
  ingested_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(ingested_at)
CLUSTER BY type, lifecycle;

CREATE TABLE IF NOT EXISTS open_harness_hub.rule (
  rule_id   STRING NOT NULL,
  pack_id   STRING NOT NULL,
  family    STRING NOT NULL,
  severity  STRING,
  category  STRING,
  pattern   STRING,
  body      JSON NOT NULL,
  enabled   BOOL DEFAULT TRUE
)
CLUSTER BY family, severity;

CREATE TABLE IF NOT EXISTS open_harness_hub.knowledge_leaf (
  leaf_id   STRING NOT NULL,
  pack_id   STRING NOT NULL,
  leaf_type STRING NOT NULL,
  industry  STRING,
  language  STRING,
  body      JSON NOT NULL,
  embedding ARRAY<FLOAT64>
)
CLUSTER BY pack_id, leaf_type;

CREATE TABLE IF NOT EXISTS open_harness_hub.run (
  run_id        STRING NOT NULL,
  artifact_id   STRING NOT NULL,
  started_at    TIMESTAMP NOT NULL,
  finished_at   TIMESTAMP,
  status        STRING NOT NULL,
  adapter_id    STRING,
  inputs        JSON,
  outputs       JSON,
  trace         JSON,
  cost_usd      NUMERIC,
  trust_boundary STRING
)
PARTITION BY DATE(started_at)
CLUSTER BY artifact_id, status;

-- Useful queries:
--   -- catalog growth over time
--   SELECT DATE(ingested_at) day, COUNT(*) FROM open_harness_hub.artifact GROUP BY 1 ORDER BY 1;
--
--   -- spend by adapter over the last 30 days
--   SELECT adapter_id, SUM(cost_usd) FROM open_harness_hub.run
--   WHERE started_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
--   GROUP BY adapter_id ORDER BY 2 DESC;
--
--   -- nearest-neighbour vector search (BigQuery ML.DISTANCE)
--   SELECT leaf_id, ML.DISTANCE(embedding, @query_vec, 'COSINE') AS dist
--   FROM   open_harness_hub.knowledge_leaf
--   ORDER BY dist
--   LIMIT 10;
