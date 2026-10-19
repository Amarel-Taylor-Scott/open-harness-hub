---
name: canonical-factory-row-bulk-load
description: Prepare high-volume generated-object shards for canonical Postgres storage
  with relationship checks before psql bulk loading.
when_to_use: 'Pipeline kind: serving.'
---

# Canonical factory row bulk load

Runs source governance, local relationship preflight, CSV bulk export, and object count reporting for generated-object rows that cover entities, dedupe, labels, dimensions, embeddings, review tickets, and index records.

## Task

Prepare high-volume generated-object shards for canonical Postgres storage with relationship checks before psql bulk loading.

## Steps

1. **source-governance** — `tool` → `tool/source-record-governance-router`
2. **relationship-preflight** — `tool` → `tool/factory-jsonl-relationship-preflight`
3. **bulk-copy-export** — `tool` → `tool/factory-jsonl-bulk-copy-loader`
4. **count-staged-and-canonical** — `tool` → `tool/object-count-report-generator`

## Defaults

- **knowledge_packs**: `knowledge-pack/canonical-factory-row-patterns`, `knowledge-pack/bulk-generated-object-load-patterns`

## Success criteria

- deterministic `$.relationship_preflight_report.ok` == `True`
- deterministic `$.bulk_load_manifest.load_sql` is_truthy `True`
- semantic must_cover ['source governance', 'dedupe clusters', 'entity references', 'labels and dimensions', 'review tickets', 'index records'] against `$.bulk_load_manifest`

## Provenance

- Hub component: `pipeline/canonical-factory-row-bulk-load` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, finance.aml, cross_industry
- Full source manifest: see `references/manifest.yaml`
