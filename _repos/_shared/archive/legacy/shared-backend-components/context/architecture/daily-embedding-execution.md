# Daily Embedding Execution

Daily component generation now produces thousands of `object_embedding` rows. Those rows are work orders, not stored vectors. The daily embedding execution planner turns the work rows into retryable batches, records model profiles and costs, and runs a vector readiness audit.

## Command

```bash
python3 -m scripts.db.daily_embedding_execution_batch_plan \
  --daily-run-dir dist/daily-production-runs/2026-05-31 \
  --output-dir dist/daily-embedding-execution/2026-05-31 \
  --run-id daily-embedding-2026-05-31
```

## What It Emits

- `embedding-model-profiles.json`;
- `embedding-plan/embedding-batches.jsonl`;
- `embedding-plan/embedding-completion-stubs.jsonl`;
- `embedding-plan/embedding-execution-plan.json`;
- `vector-readiness/vector-readiness-summary.json`;
- `daily-embedding-execution-batch-plan.json`.

## Current 5K Result

The `2026-05-31` embedding plan produced:

- 5,000 input embedding rows;
- 41 planned local embedding batches;
- 5,000 planned completion rows;
- 958,440 estimated tokens;
- 0.0 estimated token-priced USD for the default local profile;
- 5,000 missing vector rows in the readiness audit;
- `not_ready` vector readiness status.

That is the intended state before worker execution. The system has planned work, but it should not advertise vector search readiness until workers store vectors and the readiness audit passes.

## Execution Boundary

This planner does not call embedding providers, write vectors, or connect to Postgres. It only creates sharded work and readiness evidence. Actual workers can be local, Render workers, Cloud Run jobs, or hosted APIs, but they must write stored vector metadata for the readiness audit.

## Next Actions

1. Dispatch `embedding-batches.jsonl` to local workers by default.
2. Replace hosted placeholder pricing with a live pricing snapshot before external execution.
3. Write stored vector metadata after worker completion.
4. Rerun vector readiness before active promotion or tenant-visible vector search.
