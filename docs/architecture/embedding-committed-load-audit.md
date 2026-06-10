# Embedding Committed Load Audit

The embedding committed load audit is the final side-effect-free readiness gate before vector search can be considered product-ready. It compares four layers:

1. planned embedding completion rows;
2. stored vector readiness rows;
3. pgvector load-plan accepted and rejected rows;
4. committed Postgres `object_embedding` counts.

This avoids treating JSONL evidence as if it were already live product data.

## Inputs

- `embedding-execution-plan.json`
- `vector-readiness-summary.json`
- `pgvector-embedding-load-plan-summary.json`
- optional committed count rows from `db/postgres/object_count_report.sql`

## Daily Command Before Applying SQL

```bash
python3 -m scripts.db.embedding_committed_load_audit \
  --embedding-execution-plan dist/daily-embedding-execution/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json \
  --vector-readiness-summary dist/local-hash-embedding-worker/YYYY-MM-DD/vector-readiness/vector-readiness-summary.json \
  --pgvector-load-plan-summary dist/pgvector-embedding-load-plan/YYYY-MM-DD/pgvector-embedding-load-plan-summary.json \
  --output dist/pgvector-embedding-load-plan/YYYY-MM-DD/embedding-committed-load-audit.json \
  --run-id embedding-committed-load-YYYY-MM-DD
```

Expected status before SQL is applied:

- `audit_status`: `load_planned_not_committed`
- `vector_search_product_ready`: `false`

## Daily Command After Applying SQL

```bash
psql "$DATABASE_URL" -f db/postgres/object_count_report.sql --csv \
  | python3 scripts/db/psql_csv_to_count_json.py \
      --output dist/pgvector-embedding-load-plan/YYYY-MM-DD/committed-counts.json

python3 -m scripts.db.embedding_committed_load_audit \
  --embedding-execution-plan dist/daily-embedding-execution/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json \
  --vector-readiness-summary dist/local-hash-embedding-worker/YYYY-MM-DD/vector-readiness/vector-readiness-summary.json \
  --pgvector-load-plan-summary dist/pgvector-embedding-load-plan/YYYY-MM-DD/pgvector-embedding-load-plan-summary.json \
  --committed-counts dist/pgvector-embedding-load-plan/YYYY-MM-DD/committed-counts.json \
  --output dist/pgvector-embedding-load-plan/YYYY-MM-DD/embedding-committed-load-audit.json \
  --run-id embedding-committed-load-YYYY-MM-DD
```

Expected status after committed counts cover the accepted load rows:

- `audit_status`: `verified`
- `vector_search_product_ready`: `true`

## Current Evidence

The `2026-05-31` run shows the pre-commit state:

- `planned_completion_rows`: 5000
- `vector_readiness_ready_rows`: 256
- `pgvector_load_accepted_rows`: 256
- `pgvector_load_rejected_rows`: 0
- `audit_status`: `load_planned_not_committed`
- `vector_search_product_ready`: `false`

A simulated committed-count file with `object_embedding=256` verifies the positive path and returns `audit_status: verified`.
