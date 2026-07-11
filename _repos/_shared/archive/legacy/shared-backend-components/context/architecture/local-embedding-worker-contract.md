# Local Embedding Worker Contract

This stage turns a daily embedding execution plan into a bounded worker contract test. It proves that a worker can read planned completion rows, emit stored vector metadata rows, and pass the vector readiness audit before we enable production semantic embedding writes.

The contract deliberately does not compute real embeddings. Rows are marked `contract_stub: true` and `storage_backend: contract_stub` so they cannot be treated as tenant-visible vector search data.

## Inputs

- `embedding-execution-plan.json`
- `embedding-batches.jsonl`
- `embedding-completion-stubs.jsonl`

## Outputs

- `sampled-embedding-completion-stubs.jsonl`
- `stored-vector-contract-rows.jsonl`
- `vector-readiness/vector-readiness-summary.json`
- `local-embedding-worker-contract-summary.json`

Each stored row preserves:

- `embedding_id`
- `subject_id`
- `subject_type`
- `batch_id`
- `profile_id`
- `text_hash`
- `dimensions`
- `expected_dimensions`
- `worker_id`
- `storage_backend`

## Daily Command

```bash
python3 -m scripts.db.local_embedding_worker_contract \
  --embedding-plan dist/daily-embedding-execution/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json \
  --output-dir dist/local-embedding-worker-contract/YYYY-MM-DD \
  --run-id local-embedding-contract-YYYY-MM-DD \
  --limit 256
```

## Current Evidence

The `2026-05-31` sample checked 256 planned completion rows and emitted 256 stored vector metadata rows. The readiness audit returned:

- `readiness_status`: `ready`
- `ready_rows`: 256
- `missing_vector_rows`: 0
- `dimension_mismatch_rows`: 0
- `text_hash_mismatch_rows`: 0
- `orphan_stored_rows`: 0

## Promotion Rule

This contract only proves shape and audit compatibility. Production promotion still requires actual embedding computation or database vector writes, plus a full vector readiness audit over the same completion set.
