# Pgvector Embedding Load Plan

This stage converts stored vector JSONL rows into reviewable SQL for the canonical `object_embedding` table. It is the bridge between local or hosted embedding workers and Postgres plus pgvector.

The planner is side-effect free. It does not connect to a database. It writes load SQL, accepted row evidence, rejected row evidence, and operator commands that can be reviewed before execution.

## Inputs

- `stored-vector-rows.jsonl`
- source `object-embeddings.jsonl`
- canonical schema dimension, currently `384`

The source embedding rows are required because the operational `object_embedding` table stores both `text` and `embedding`. Stored vector rows keep text hashes and ids; the load planner joins the original text by `embedding_id`.

## Outputs

- `object-embedding-load.sql`
- `accepted-object-embedding-load-rows.jsonl`
- `rejected-object-embedding-load-rows.jsonl`
- `pgvector-embedding-load-plan-summary.json`

Rows are rejected before SQL emission when:

- the embedding id is missing;
- the vector is missing;
- the vector length disagrees with row dimensions;
- row dimensions do not match the canonical `vector(384)` schema;
- source text cannot be joined by embedding id.

## Daily Command

```bash
python3 -m scripts.db.pgvector_embedding_load_plan \
  --stored-vectors-jsonl dist/local-hash-embedding-worker/YYYY-MM-DD/stored-vector-rows.jsonl \
  --source-embedding-rows-jsonl dist/daily-production-runs/YYYY-MM-DD/load-audit/merged-jsonl/object-embeddings.jsonl \
  --output-dir dist/pgvector-embedding-load-plan/YYYY-MM-DD \
  --run-id pgvector-embedding-load-YYYY-MM-DD
```

## Current Evidence

The `2026-05-31` sample loaded the local hash worker output into a side-effect-free SQL plan:

- `input_stored_vector_rows`: 256
- `accepted_rows`: 256
- `rejected_rows`: 0
- `schema_dimensions`: 384

## Execution Boundary

The next operator step is explicit:

```bash
psql "$DATABASE_URL" -f db/postgres/schema.sql
psql "$DATABASE_URL" -f dist/pgvector-embedding-load-plan/YYYY-MM-DD/object-embedding-load.sql
psql "$DATABASE_URL" -c "select embedding_model, count(*) from object_embedding group by embedding_model order by embedding_model;"
```

This keeps the cheap default hosting shape intact: Postgres plus pgvector remains the canonical product store, while JSONL remains the safe review and replay layer.
