# Daily Promotion Readiness

The daily production factory can now generate and audit 5,000 component candidates in a single run. The next bottleneck is promotion governance. The promotion readiness planner separates two decisions that should not be collapsed:

- candidate-table load readiness;
- tenant-visible active component promotion readiness.

## Command

```bash
python3 -m scripts.db.daily_promotion_readiness_plan \
  --daily-run-dir dist/daily-production-runs/2026-05-31 \
  --output-dir dist/daily-promotion-readiness/2026-05-31 \
  --run-id promotion-readiness-2026-05-31
```

The same planner can be reused for model-ops, source-surface, and future worker-fleet runs by passing an explicit run summary:

```bash
python3 -m scripts.db.daily_promotion_readiness_plan \
  --daily-run-dir dist/model-ops-daily-runs/2026-05-26 \
  --run-summary dist/model-ops-daily-runs/2026-05-26/model-ops-daily-run-summary.json \
  --output-dir dist/model-ops-daily-runs/2026-05-26/promotion-readiness \
  --run-id model-ops-daily-2026-05-26-promotion-readiness
```

## What It Checks

For every staged normalized object, the planner checks:

- source record link;
- dedupe cluster link;
- content hash;
- at least five index records;
- embedding work record;
- review ticket count;
- risk tier;
- active promotion blockers.

## Current 5K Result

The `2026-05-31` readiness run found:

- 5,000 staged normalized objects;
- 5,000 candidates structurally ready for candidate-table loading;
- 0 structurally blocked candidates;
- 5,000 candidates requiring embedding execution before active vector-backed publication;
- 2,000 candidates requiring review;
- 0 candidates ready for active component promotion.

That is the intended boundary. The staged rows can move toward candidate-table loading, but active components should wait for real embeddings and review resolution.

## Current Model-Ops 1K Result

The `2026-05-26` model-ops readiness run found:

- 1,000 staged normalized model/runtime/training component candidates;
- 1,000 candidates structurally ready for candidate-table loading;
- 0 structurally blocked candidates;
- 1,000 candidates requiring embedding execution before active vector-backed publication;
- 833 candidates requiring review;
- 0 candidates ready for active component promotion.

This keeps the daily run additive without pretending that staged rows are active product inventory. The row families can proceed toward candidate-table loading and vector execution, while review-heavy runtime, training, and sharing components remain blocked from tenant-visible promotion.

This run also exposed and fixed an upstream speed hazard: long generated seed IDs were previously truncated into duplicate candidate IDs, causing some rows and index records to collapse during merge. Future model-ops batches now add stable hash suffixes to generated seed IDs, normalized object IDs, and index record IDs so the factory can preserve 1,000+ daily candidates without manual repair.

## Outputs

The planner writes:

- `promotion-readiness.jsonl`;
- `promotion-review-queue.jsonl`;
- `daily-promotion-readiness-plan.json`.

It does not connect to Postgres, apply SQL, publish components, or alter staged data.

## Next Actions

1. Review and approve candidate-table load SQL from the daily production run.
2. Execute real embeddings for `object_embedding` rows.
3. Resolve review tickets for high-risk rows.
4. Run content approval and approved component promotion planners only on reviewed subsets.
