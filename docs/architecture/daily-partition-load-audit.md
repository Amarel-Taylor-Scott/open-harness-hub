# Daily Partition Load Audit

The daily component factory now emits database-ready row families. The next scale risk is count inflation: two daily partitions can share source records, canonical entities, labels, or other stable IDs. A raw line count is useful for throughput, but it is not the same as the number of rows that will exist after Postgres upsert.

## Load-Audit Shape

The load audit package does four things:

1. reads one or more daily partition directories;
2. merges each row family by its canonical table primary key;
3. runs local relationship preflight over the merged rows;
4. emits CSV files, `load.sql`, and a staged-versus-committed audit.

The output remains `staged_only` until an operator runs the generated SQL against Postgres and supplies committed row counts from `db/postgres/object_count_report.sql`.

## Current Run

The first multi-partition audit covers the first two daily batches:

```bash
python3 -m scripts.db.daily_partition_load_audit \
  --partition dist/daily-component-batch/2026-05-26 \
  --partition dist/daily-component-batch/2026-05-27 \
  --output-dir dist/daily-component-batch-load-audit/2026-05-26_to_2026-05-27 \
  --run-id daily-2026-05-26-to-2026-05-27
```

It writes:

- merged JSONL row families;
- a relationship preflight report;
- CSV files for Postgres `\copy`;
- `bulk-copy/load.sql`;
- `load-plan-manifest.json`;
- `staged-vs-committed-audit.json`;
- `summary.json`.

The first run produced:

- 114,374 raw staged rows across the two partitions;
- 114,323 unique rows after primary-key merge;
- 51 duplicate staged rows collapsed before bulk export;
- 2,000 normalized component candidates;
- 10,000 index records;
- 2,000 embedding work rows;
- 27,000 label assignments;
- 14,000 dimension values;
- 55,800 object/entity references;
- 880 review tickets;
- 0 local relationship preflight issues.

The bulk package is ready for operator review at:

```text
dist/daily-component-batch-load-audit/2026-05-26_to_2026-05-27/bulk-copy/load.sql
```

## Proof Boundary

There are three different counts:

- public component definitions in `catalog/`;
- staged database rows in daily JSONL and bulk CSV;
- committed canonical rows in Postgres.

Only committed canonical rows prove database state. The staged audit proves that a batch is internally consistent and ready for an operator-approved load.

## Why This Matters

At million-component scale, additive daily generation will repeatedly encounter shared sources, shared entities, and shared labels. Deduplicating before bulk export keeps expected Postgres counts honest and prevents dashboards from mistaking raw generated lines for committed reusable components.
