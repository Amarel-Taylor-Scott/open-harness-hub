# Theory Local Postgres Smoke

The theory local Postgres smoke plan is the operator-review bridge from staged JSONL and generated SQL to committed local database evidence. It does not execute Docker or `psql`; it emits commands and output paths so a human can review the target database and SQL before mutation.

## Command

```bash
python3 -m scripts.db.theory_local_postgres_smoke_plan \
  --theory-batch-summary dist/theory-component-batch/YYYY-MM-DD/theory-component-batch-summary.json \
  --theory-load-audit-summary dist/theory-component-batch-load-audit/YYYY-MM-DD/summary.json \
  --pgvector-load-plan-summary dist/theory-pgvector-embedding-load-plan/YYYY-MM-DD/pgvector-embedding-load-plan-summary.json \
  --embedding-execution-plan dist/theory-batch-governance-bridge/YYYY-MM-DD/embedding/embedding-plan/embedding-execution-plan.json \
  --vector-readiness-summary dist/theory-local-hash-embedding-worker/YYYY-MM-DD/vector-readiness/vector-readiness-summary.json \
  --output-dir dist/theory-local-postgres-smoke/YYYY-MM-DD \
  --run-id theory-local-postgres-smoke-YYYY-MM-DD
```

## What It Emits

The plan includes commands to:

- start the local pgvector container;
- initialize the canonical schema;
- apply the theory candidate-row bulk load SQL;
- apply the theory vector load SQL;
- export committed counts;
- rerun staged-vs-committed load audit;
- rerun embedding committed-load audit.

This keeps generated, staged, load-planned, and committed states separate. Active promotion remains blocked until review queues are resolved and committed-count audits prove the expected rows exist.
