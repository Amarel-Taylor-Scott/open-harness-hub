---
name: factory-jsonl-bulk-copy-load
description: Bulk-load high-volume generated OpenHubForAI objects into canonical Postgres
  tables without inflating YAML manifests.
when_to_use: 'Pipeline kind: serving.'
---

# Factory JSONL bulk COPY load

Converts validated generated-object JSONL shards into CSV staging files and a psql bulk load script for canonical Postgres storage.

## Task

Bulk-load high-volume generated OpenHubForAI objects into canonical Postgres tables without inflating YAML manifests.

## Steps

1. **privacy-and-source-gate** — `tool` → `tool/source-record-governance-router`
2. **export-bulk-copy** — `tool` → `tool/factory-jsonl-bulk-copy-loader`
3. **count-staged-rows** — `tool` → `tool/object-count-report-generator`
4. **count-canonical-rows** — `tool` → `tool/postgres-object-count-sql` (when `database_url is present`)

## Defaults

- **knowledge_packs**: `knowledge-pack/bulk-generated-object-load-patterns`, `knowledge-pack/postgres-pgvector-bootstrap-patterns`

## Success criteria

- deterministic `$.bulk_load_manifest.load_sql` is_truthy `True`
- semantic must_cover ['CSV staging files', 'psql copy', 'upsert into canonical Postgres tables'] against `$.bulk_load_manifest`

## Provenance

- Hub component: `pipeline/factory-jsonl-bulk-copy-load` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
