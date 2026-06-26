---
name: source-surface-seeds-to-factory-rows
description: Export source-surface seeds into canonical JSONL row families ready for
  relationship preflight and Postgres bulk-copy loading.
when_to_use: 'Pipeline kind: research_web.source_surface_seed_factory_rows.'
---

# Source surface seeds to factory rows

Converts esoteric industry source-surface seeds into canonical factory row families with source governance, entity refs, fuzzy dedupe, embedding stubs, review tickets, and index records.

## Task

Export source-surface seeds into canonical JSONL row families ready for relationship preflight and Postgres bulk-copy loading.

## Steps

1. **govern-source-surface-seeds** — `tool` → `tool/source-record-governance-router`
2. **export-source-surface-row-families** — `tool` → `tool/source-surface-seed-row-exporter`
3. **preflight-row-relationships** — `tool` → `tool/factory-jsonl-relationship-preflight`
4. **prepare-bulk-copy** — `tool` → `tool/factory-jsonl-bulk-copy-loader`

## Defaults

- **knowledge_packs**: `knowledge-pack/esoteric-industry-source-surfaces`, `knowledge-pack/source-surface-seed-row-patterns`, `knowledge-pack/use-case-seed-row-patterns`

## Success criteria

- semantic must_cover ['normalized_object', 'canonical_entity', 'object_entity_ref', 'object_embedding', 'review_ticket', 'index_record'] against `$.row_counts`

## Provenance

- Hub component: `pipeline/source-surface-seeds-to-factory-rows` v0.1.0
- License: `MIT`
- Industry: automotive, energy, manufacturing, construction, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
