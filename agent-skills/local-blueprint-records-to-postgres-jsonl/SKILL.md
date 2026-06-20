---
name: local-blueprint-records-to-postgres-jsonl
description: Convert a local sentence-to-pipeline run into canonical source, object,
  entity, dedupe, review, and index JSONL shards that can be loaded into Postgres/pgvector.
when_to_use: 'Pipeline kind: meta_build.local_blueprint_persistence.'
---

# Local blueprint records to Postgres JSONL

Exports local sentence-to-pipeline demo output records into canonical JSONL row families and prepares them for the existing Postgres bulk-copy loader.

## Task

Convert a local sentence-to-pipeline run into canonical source, object, entity, dedupe, review, and index JSONL shards that can be loaded into Postgres/pgvector.

## Steps

1. **govern-source-prompt** — `tool` → `tool/source-record-governance-router`
2. **run-local-demo** — `tool` → `tool/sentence-to-pipeline-blueprint-runner`
3. **emit-output-records** — `pipeline` → `pipeline/local-sentence-blueprint-output-records`
4. **export-jsonl-row-families** — `tool` → `tool/blueprint-record-jsonl-exporter`
5. **preflight-row-relationships** — `tool` → `tool/factory-jsonl-relationship-preflight`
6. **prepare-bulk-copy** — `tool` → `tool/factory-jsonl-bulk-copy-loader`

## Defaults

- **knowledge_packs**: `knowledge-pack/local-blueprint-record-persistence-patterns`, `knowledge-pack/local-blueprint-output-record-patterns`

## Success criteria

- semantic must_cover ['source_record', 'normalized_object', 'canonical_entity', 'dedupe_cluster', 'review_ticket', 'index_record'] against `$.row_counts`
- deterministic `$.jsonl_files` is_truthy `True`

## Provenance

- Hub component: `pipeline/local-blueprint-records-to-postgres-jsonl` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
