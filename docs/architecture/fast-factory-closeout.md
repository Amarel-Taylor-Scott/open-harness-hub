# Fast Factory Closeout

The fast closeout path reports progress from database-first factory outputs without rescanning every component definition or rebuilding every catalog page.

## Purpose

Use this after normal daily factory work to answer:

- how many public component definitions exist;
- how many database-backed component candidates were generated;
- how many unique staged rows exist;
- whether candidate load SQL exists;
- how many review tickets exist;
- how many embeddings were planned;
- how many vectors are ready;
- how many pgvector rows were accepted or rejected;
- whether committed database counts prove product readiness.

## Command

```bash
python3 -m scripts.factory.fast_factory_closeout_report \
  --output dist/fast-factory-closeout/YYYY-MM-DD/summary.json \
  --theory-batch-summary dist/theory-component-batch/YYYY-MM-DD/theory-component-batch-summary.json \
  --load-audit-summary dist/theory-component-batch-load-audit/YYYY-MM-DD/summary.json \
  --governance-bridge-summary dist/theory-batch-governance-bridge/YYYY-MM-DD/theory-batch-governance-bridge-summary.json \
  --local-vector-worker-summary dist/theory-local-hash-embedding-worker/YYYY-MM-DD/local-hash-embedding-worker-summary.json \
  --pgvector-load-plan-summary dist/theory-pgvector-embedding-load-plan/YYYY-MM-DD/pgvector-embedding-load-plan-summary.json \
  --embedding-committed-load-audit dist/theory-pgvector-embedding-load-plan/YYYY-MM-DD/embedding-committed-load-audit.json \
  --local-postgres-smoke-plan dist/theory-local-postgres-smoke/YYYY-MM-DD/theory-local-postgres-smoke-plan.json
```

## Rule

Use this for daily progress reports. Use full validation and full catalog page rebuilds only for release gates, schema/vocabulary changes, broad reference rewires, corruption recovery, or explicit requests.
