---
name: source-governance-entity-dedupe-index
description: Prepare raw source records and extracted objects for scalable, trustworthy
  indexing by applying governance, entity linking, deduplication, and index record
  emission.
when_to_use: 'Pipeline kind: research_web.source_governance_entity_dedupe_index.'
---

# Source governance entity dedupe index

Normalize source records, apply governance routing, extract and link entities, fuzzy-dedupe objects, and emit keyword, vector, graph, facet, freshness, and review records.

## Task

Prepare raw source records and extracted objects for scalable, trustworthy indexing by applying governance, entity linking, deduplication, and index record emission.

## Steps

1. **route_source_governance** — `tool` → `tool/source-record-governance-router`
2. **link_entities** — `tool` → `tool/entity-recognition-linker`
3. **dedupe_candidates** — `tool` → `tool/fuzzy-dedupe-clusterer`
4. **emit_index_records** — `tool` → `tool/index-record-emitter`
5. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/primitive-source-surface-map`, `knowledge-pack/occupation-source-surface-map`, `knowledge-pack/procedure-knowledge-object-patterns`
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- deterministic `$.outputs.dedupe_clusters` is_truthy `True`
- deterministic `$.outputs.index_records` is_truthy `True`

## Provenance

- Hub component: `pipeline/source-governance-entity-dedupe-index` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
