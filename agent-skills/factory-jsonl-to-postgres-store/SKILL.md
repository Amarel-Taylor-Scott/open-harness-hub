---
name: factory-jsonl-to-postgres-store
description: Emit reviewable Postgres upsert SQL from validated object-factory JSONL
  shards so generated objects are stored canonically rather than left only as files.
when_to_use: 'Pipeline kind: research_web.factory_jsonl_to_postgres_store.'
---

# Factory JSONL to Postgres store

Move validated object-factory JSONL outputs into the canonical Postgres and pgvector-backed operational store through deterministic upsert SQL.

## Task

Emit reviewable Postgres upsert SQL from validated object-factory JSONL shards so generated objects are stored canonically rather than left only as files.

## Steps

1. **load_storage_patterns** — `knowledge_pack` → `knowledge-pack/generated-object-storage-patterns`
2. **emit_postgres_upserts** — `tool` → `tool/factory-jsonl-postgres-loader`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/generated-object-storage-patterns`

## Success criteria

- deterministic `$.outputs.sql_load_file` is_truthy `True`

## Provenance

- Hub component: `pipeline/factory-jsonl-to-postgres-store` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
