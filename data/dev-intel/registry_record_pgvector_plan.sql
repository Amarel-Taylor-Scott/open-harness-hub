-- pgvector storage + search for registry records (generated; vector dim from registry.records.EMBED_DIM).
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS registry_record (
  id            text PRIMARY KEY,
  registry      text NOT NULL,
  name          text NOT NULL,
  description   text,
  metadata      jsonb,
  embedding     vector(64),
  synthetic     boolean NOT NULL DEFAULT false,
  candidate     boolean NOT NULL DEFAULT true,   -- discovery != trust; promotion boundary applies
  serves_truth  boolean NOT NULL DEFAULT false
);
CREATE INDEX IF NOT EXISTS registry_record_registry_idx ON registry_record (registry);
CREATE INDEX IF NOT EXISTS registry_record_embedding_idx ON registry_record USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- load: stream JSONL -> COPY/INSERT (the population engine), then ANALYZE; vector search:
--   SELECT id, name, 1 - (embedding <=> :query_vec) AS score FROM registry_record
--   WHERE (:registry IS NULL OR registry = :registry) ORDER BY embedding <=> :query_vec LIMIT :k;
