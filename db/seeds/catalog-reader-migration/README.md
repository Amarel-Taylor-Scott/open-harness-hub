# Catalog Reader Migration Seed Package

This directory contains database-ready seed rows for the
`catalog_reader_migration_candidate` table in `db/postgres/schema.sql`.

The package makes direct catalog YAML readers explicit:

```text
Seed/export readers may remain file-backed.
Runtime and product-facing readers should move toward database row sources.
```

## Files

```text
catalog_reader_migration_candidate.jsonl
load-catalog-reader-migration-candidates.sql
```

Each row records:

- source path
- reader classification
- migration status
- priority
- recommended action
- matched YAML-reading patterns
- line samples
- owner team

## Rules

- `operational_migration_candidate` rows should be migrated to
  `catalog_row_source.py` or a database-backed equivalent.
- `row_backed_consumer` rows may keep YAML as a static/local fallback.
- `seed_export_validation`, `seed_export_bridge`, and draft-generation rows are
  allowed to remain file-backed by design.
- `unknown_yaml_reader` rows require manual classification before release.
