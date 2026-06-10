# Local Hash Embedding Worker

The local hash embedding worker is the first executable vector-producing worker in the daily component factory. It reads an embedding execution plan, joins planned completion rows back to source `object_embedding` text rows, generates deterministic fixed-dimension vectors, and writes pgvector-ready JSONL rows.

This worker is intentionally dependency-free. It does not download a model, call a provider, or require network access. It gives the platform an immediate replayable vector execution path while the production semantic embedding workers are still being selected.

## What It Produces

- `completed-embedding-rows.jsonl`
- `stored-vector-rows.jsonl`
- `vector-readiness/vector-readiness-summary.json`
- `local-hash-embedding-worker-summary.json`

Each stored vector row includes:

- `embedding_id`
- `subject_id`
- `subject_type`
- `batch_id`
- `profile_id`
- `text_hash`
- `dimensions`
- `vector`
- `worker_id`
- `storage_backend`
- `embedding_runtime`
- `embedding_model`

## Daily Command

```bash
python3 -m scripts.db.local_hash_embedding_worker \
  --embedding-plan dist/daily-embedding-execution/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json \
  --output-dir dist/local-hash-embedding-worker/YYYY-MM-DD \
  --run-id local-hash-embedding-YYYY-MM-DD \
  --limit 256
```

## Current Evidence

The `2026-05-31` sample processed 256 planned completion rows:

- `completed_embedding_rows`: 256
- `stored_vector_rows`: 256
- `missing_text_rows`: 0
- `readiness_status`: `ready`
- `missing_vector_rows`: 0
- `dimension_mismatch_rows`: 0
- `text_hash_mismatch_rows`: 0
- `orphan_stored_rows`: 0

## Quality Boundary

Hashing vectors are useful for validating worker orchestration, row contracts, pgvector load shape, replay behavior, and readiness checks. They should not be treated as a final semantic search model without evaluation. The next production step is to add workers for sentence-transformers, TEI, vLLM, hosted embedding APIs, or BigQuery vector workflows using the same completion and stored-vector row contract.
