---
name: use-case-seeds-to-entity-ref-rows
description: Convert cross-domain use-case seed metadata into canonical entity and
  object_entity_ref rows that can drive graph search, blocking, dedupe, and pipeline
  assembly.
when_to_use: 'Pipeline kind: research_web.use_case_seed_entity_ref_rows.'
---

# Use case seeds to entity ref rows

Promotes cross-domain use-case seed domains, flexible label paths, inputs, outputs, required stages, and risk tiers into canonical entity and object_entity_ref rows for graph search and comparison blocking.

## Task

Convert cross-domain use-case seed metadata into canonical entity and object_entity_ref rows that can drive graph search, blocking, dedupe, and pipeline assembly.

## Steps

1. **govern-use-case-seeds** — `tool` → `tool/source-record-governance-router`
2. **export-entity-ref-rows** — `tool` → `tool/use-case-seed-entity-ref-exporter`
3. **preflight-entity-relationships** — `tool` → `tool/factory-jsonl-relationship-preflight`
4. **prepare-bulk-copy** — `tool` → `tool/factory-jsonl-bulk-copy-loader`

## Defaults

- **knowledge_packs**: `knowledge-pack/cross-domain-use-case-seeds`, `knowledge-pack/use-case-seed-entity-ref-patterns`, `knowledge-pack/flexible-hierarchy-label-patterns`

## Success criteria

- semantic must_cover ['canonical_entity', 'object_entity_ref', 'graph index records', 'comparison blocking'] against `$.row_counts`
- deterministic `$.row_counts.object_entity_ref` > `0`

## Provenance

- Hub component: `pipeline/use-case-seeds-to-entity-ref-rows` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, finance, legal, media, creative, energy, healthcare, cross_industry
- Full source manifest: see `references/manifest.yaml`
