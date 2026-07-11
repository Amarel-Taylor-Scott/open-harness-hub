# Local Pgvector Embedding Smoke

The local pgvector embedding smoke plan is the first operator-ready path for proving that generated embedding SQL can actually land in Postgres. The planner remains side-effect free: it writes commands and expected files, but it does not start Docker, run `psql`, or mutate a database.

## Inputs

- `pgvector-embedding-load-plan-summary.json`
- `embedding-execution-plan.json`
- `vector-readiness-summary.json`
- `infra/postgres/docker-compose.pgvector.yml`
- `db/postgres/schema.sql`
- `db/postgres/object_count_report.sql`

## Planned Commands

The generated plan emits commands to:

1. start local pgvector through Docker Compose;
2. wait for `pg_isready`;
3. set the local development `DATABASE_URL`;
4. initialize the schema;
5. apply `object-embedding-load.sql`;
6. export committed count rows;
7. rerun the embedding committed-load audit.

## Daily Command

```bash
python3 -m scripts.db.local_pgvector_embedding_smoke_plan \
  --pgvector-load-plan-summary dist/pgvector-embedding-load-plan/YYYY-MM-DD/pgvector-embedding-load-plan-summary.json \
  --embedding-execution-plan dist/daily-embedding-execution/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json \
  --vector-readiness-summary dist/local-hash-embedding-worker/YYYY-MM-DD/vector-readiness/vector-readiness-summary.json \
  --output-dir dist/local-pgvector-embedding-smoke/YYYY-MM-DD \
  --run-id local-pgvector-embedding-smoke-YYYY-MM-DD
```

## Current Evidence

The `2026-05-31` plan produced seven reviewed commands and reported:

- `accepted_load_rows`: 256
- `rejected_load_rows`: 0
- `safe_to_smoke_apply`: true

## Execution Boundary

The output is a plan, not execution. Operators should only run it against an intended local pgvector container. Managed Postgres or Render targets should use a separate execution plan with the correct `DATABASE_URL` and permission boundary.
