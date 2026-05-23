-- ----------------------------------------------------------------------------
-- Open Harness Hub — SQLite + sqlite-vec (embedded vector search)
--
-- sqlite-vec is a SQLite extension that adds native VECTOR columns and
-- approximate-nearest-neighbor search. Pair with db/sqlite/schema.sql for a
-- single-file, zero-deps catalog + vector store. Spec: https://github.com/asg017/sqlite-vec
-- ----------------------------------------------------------------------------

-- Load sqlite-vec extension at connection time:
--   sqlite3 catalog.db
--   .load ./vec0

-- Catalog index — one vector per artifact (name + description + tags).
CREATE VIRTUAL TABLE IF NOT EXISTS catalog_vec USING vec0(
  artifact_id     TEXT PRIMARY KEY,
  embedding       FLOAT[384],                  -- adjust dim to match your embedder
  +type           TEXT,
  +industry_csv   TEXT,
  +capability_csv TEXT,
  +modality_csv   TEXT,
  +lifecycle      TEXT,
  +trust_boundary TEXT
);

-- Knowledge-leaf index — one vector per RAG document / rule.
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_vec USING vec0(
  leaf_id         TEXT PRIMARY KEY,
  embedding       FLOAT[384],
  +pack_id        TEXT,
  +leaf_type      TEXT,
  +industry       TEXT,
  +language       TEXT
);

-- Sample query (KNN with metadata filter):
--   SELECT leaf_id, distance
--   FROM   knowledge_vec
--   WHERE  pack_id = 'knowledge-pack/icd10-sample'
--     AND  embedding MATCH :query_vector
--   ORDER BY distance
--   LIMIT 10;
