---
name: use-case-seeds-to-label-dimension-rows
description: Convert cross-domain use-case seeds into loadable candidate primitive,
  label, dimension, dedupe, review, and index JSONL row families while excluding insurance
  scope.
when_to_use: 'Pipeline kind: research_web.use_case_seed_label_dimension_rows.'
---

# Use case seeds to label and dimension rows

Exports broad use-case seeds into candidate primitive rows, flexible hierarchy labels, dimensions, canonical entities, object_entity_refs, object_embedding stubs, dedupe clusters, review tickets, and index records for Postgres/pgvector loading.

## Task

Convert cross-domain use-case seeds into loadable candidate primitive, label, dimension, dedupe, review, and index JSONL row families while excluding insurance scope.

## Steps

1. **govern-use-case-seeds** — `tool` → `tool/source-record-governance-router`
2. **export-seed-row-families** — `tool` → `tool/use-case-seed-row-exporter`
3. **link-seed-entities** — `tool` → `tool/entity-recognition-linker`
4. **preflight-row-relationships** — `tool` → `tool/factory-jsonl-relationship-preflight`
5. **prepare-bulk-copy** — `tool` → `tool/factory-jsonl-bulk-copy-loader`

## Defaults

- **knowledge_packs**: `knowledge-pack/cross-domain-use-case-seeds`, `knowledge-pack/use-case-seed-row-patterns`, `knowledge-pack/use-case-seed-entity-ref-patterns`, `knowledge-pack/use-case-seed-embedding-bucket-patterns`, `knowledge-pack/flexible-hierarchy-label-patterns`

## Success criteria

- semantic must_cover ['normalized_object', 'label_assignment', 'dimension_value', 'canonical_entity', 'object_entity_ref', 'object_embedding', 'review_ticket', 'index_record'] against `$.row_counts`
- deterministic `$.bulk_load_plan` is_truthy `True`

## Provenance

- Hub component: `pipeline/use-case-seeds-to-label-dimension-rows` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, finance, legal, media, creative, energy, healthcare, cross_industry
- Full source manifest: see `references/manifest.yaml`
