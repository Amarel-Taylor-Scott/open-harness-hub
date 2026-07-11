# Duplicate Collapse Report

Daily factories need a faster signal than a late load-audit surprise. Duplicate collapse reporting groups staged row families by database primary key and explains what would be collapsed before bulk loading.

The report separates normal shared-reference duplicates from dangerous component candidate collisions.

## What It Checks

For each staged row family, the reporter records:

- raw row count;
- unique primary-key count;
- duplicate rows collapsed;
- duplicate key groups;
- identical versus conflicting duplicate rows;
- ID source classification such as hash-suffixed IDs, truncation-risk IDs, shared source records, shared entities, and composite keys;
- risk tier for the row family.

Critical families are:

- normalized component candidates;
- embedding work rows;
- index records.

Duplicates in those families are more likely to indicate ID truncation, hash collision, partial generation, or worker replay errors. Shared source records, canonical entities, and object/entity references can be normal when many components use the same source surface or hierarchy.

## Command

```bash
python3 -m scripts.db.duplicate_collapse_report \
  --partition dist/model-ops-daily-runs/2026-05-26 \
  --output-dir dist/model-ops-daily-runs/2026-05-26/duplicate-collapse \
  --run-id model-ops-daily-2026-05-26-duplicate-collapse
```

## Current Model-Ops Result

The `2026-05-26` model-ops batch reports:

- 0 duplicate rows collapsed;
- 0 duplicate normalized component candidates;
- 0 duplicate embedding work rows;
- 0 duplicate index records;
- 0 duplicate review tickets;
- 0 conflicting duplicate key groups.

The first run of this reporter found 492 collapsed review-ticket rows caused by truncation-only review ticket IDs. The generator now uses stable hash-suffixed review IDs, so the current model-ops batch preserves all 833 review tickets and the load audit reports zero duplicate collapse.

## Proof Boundary

This report is read-only. It does not repair rows, apply SQL, update Postgres, or mutate indexes.

Recommended order for daily runs:

1. generate row families;
2. run duplicate collapse reporting;
3. run load audit;
4. run index coverage repair;
5. run promotion readiness;
6. run approved database load only after operator review.
