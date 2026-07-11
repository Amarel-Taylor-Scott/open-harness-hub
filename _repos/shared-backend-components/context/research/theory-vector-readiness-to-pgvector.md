# Theory Vector Readiness To Pgvector

Theory-derived components should not become tenant-visible search results just because they were generated. The vector path has four distinct states:

- embedding work planned;
- local vectors generated and readiness-audited;
- pgvector load SQL emitted and reviewed;
- committed Postgres counts verified.

Only the final state makes vector search product-ready.

## Current Command Sequence

```bash
python3 -m scripts.db.local_hash_embedding_worker \
  --embedding-plan dist/theory-batch-governance-bridge/YYYY-MM-DD/embedding/embedding-plan/embedding-execution-plan.json \
  --output-dir dist/theory-local-hash-embedding-worker/YYYY-MM-DD \
  --run-id theory-local-hash-embedding-YYYY-MM-DD \
  --limit 1000
```

```bash
python3 -m scripts.db.pgvector_embedding_load_plan \
  --stored-vectors-jsonl dist/theory-local-hash-embedding-worker/YYYY-MM-DD/stored-vector-rows.jsonl \
  --source-embedding-rows-jsonl dist/theory-component-batch-load-audit/YYYY-MM-DD/merged-jsonl/object-embeddings.jsonl \
  --output-dir dist/theory-pgvector-embedding-load-plan/YYYY-MM-DD \
  --run-id theory-pgvector-embedding-load-YYYY-MM-DD
```

```bash
python3 -m scripts.db.embedding_committed_load_audit \
  --embedding-execution-plan dist/theory-batch-governance-bridge/YYYY-MM-DD/embedding/embedding-plan/embedding-execution-plan.json \
  --vector-readiness-summary dist/theory-local-hash-embedding-worker/YYYY-MM-DD/vector-readiness/vector-readiness-summary.json \
  --pgvector-load-plan-summary dist/theory-pgvector-embedding-load-plan/YYYY-MM-DD/pgvector-embedding-load-plan-summary.json \
  --output dist/theory-pgvector-embedding-load-plan/YYYY-MM-DD/embedding-committed-load-audit.json \
  --run-id theory-embedding-committed-load-YYYY-MM-DD
```

## 2026-05-26 Evidence

The theory-derived vector path produced:

- 1,000 completed local embedding rows;
- 1,000 stored vector rows;
- 0 missing source text rows;
- vector readiness `ready`;
- 1,000 pgvector load-accepted rows;
- 0 pgvector load-rejected rows;
- committed-load audit `load_planned_not_committed`;
- vector search product-ready: false until committed Postgres counts cover the load plan.

This is the intended state before an operator applies SQL to the selected Postgres database and exports committed counts.
