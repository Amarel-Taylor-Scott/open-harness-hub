# Index Coverage Repair

High-volume component factories must not discover missing search records only after a promotion-readiness run. The index coverage repair planner checks staged component rows for the expected hybrid-search record set:

- keyword;
- vector;
- graph;
- facet;
- quality.

The planner writes repair JSONL only. It does not update Postgres, pgvector, a search service, or a graph store.

## Command

```bash
python3 -m scripts.db.index_coverage_repair_plan \
  --normalized-objects-jsonl dist/model-ops-daily-runs/2026-05-26/load-audit/merged-jsonl/normalized-objects.jsonl \
  --existing-index-records-jsonl dist/model-ops-daily-runs/2026-05-26/load-audit/merged-jsonl/index-records.jsonl \
  --object-embeddings-jsonl dist/model-ops-daily-runs/2026-05-26/load-audit/merged-jsonl/object-embeddings.jsonl \
  --object-entity-refs-jsonl dist/model-ops-daily-runs/2026-05-26/load-audit/merged-jsonl/object-entity-refs.jsonl \
  --output-dir dist/model-ops-daily-runs/2026-05-26/index-coverage-repair \
  --run-id model-ops-daily-2026-05-26-index-coverage-repair
```

## Current Model-Ops Result

After the generated-ID hash suffix fix, the `2026-05-26` model-ops batch has:

- 1,000 normalized component candidates;
- 5,000 existing index records;
- 1,000 fully covered candidates;
- 0 incomplete candidates;
- 0 missing index repair records emitted.

This is the intended fast feedback loop. If a future 1K or 5K batch loses index rows through ID truncation, duplicate collapse, partial generation, or a worker failure, the repair planner will produce explicit missing index records before promotion readiness blocks the batch.

## Proof Boundary

Index repair output is still staged data. The next gates are:

1. load preflight for generated repair rows;
2. approved candidate-table load;
3. embedding execution for vector-backed search;
4. promotion readiness;
5. review resolution before active tenant-visible publication.
