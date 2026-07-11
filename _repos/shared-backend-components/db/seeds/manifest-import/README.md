# Manifest Import Seed Package

This directory contains database-ready seed rows for the
`manifest_import_batch` and `manifest_import_record` tables in
`db/postgres/schema.sql`.

The package follows the storage direction:

```text
Catalog YAML is a reviewable seed/export artifact.
Database import records track which YAML was mapped, hashed, flagged, or held.
Hosted/runtime systems should read operational truth from database rows.
```

## Files

```text
manifest_import_batch.jsonl
manifest_import_record.jsonl
load-manifest-import-records.sql
```

`manifest_import_record.jsonl` records one row per catalog manifest with:

- component id and type
- manifest path and content hash
- lifecycle/freshness metadata
- import status
- recommended action
- rotted-context or migration flags
- row-count hints for expanded database rows

The generated SQL is a reviewable psql load example:

```bash
psql "$DATABASE_URL" -f db/seeds/manifest-import/load-manifest-import-records.sql
```

## Rules

- These rows do not delete or rewrite YAML files.
- `review`, `archive_seed`, and `hold` actions require curator review.
- Version-like slugs are tracked as migration candidates; published ids must not
  be silently renamed.
- The import batch id is deterministic for seed/export review and should be
  changed only when a deployment wants separate historical batches.
