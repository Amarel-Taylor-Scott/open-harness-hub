---
name: task-marketplace-archetype-intake
description: Normalize task-marketplace metadata into reusable workflow primitives
  while preserving privacy, provenance, license review, dedupe, index, and review-ticket
  boundaries.
when_to_use: 'Pipeline kind: research_web.task_marketplace_archetype_intake.'
---

# Task marketplace archetype intake

Turn task-marketplace metadata or user exports into reusable task archetype primitives with privacy gates, entity records, dedupe clusters, index records, and review tickets.

## Task

Normalize task-marketplace metadata into reusable workflow primitives while preserving privacy, provenance, license review, dedupe, index, and review-ticket boundaries.

## Steps

1. **load_task_marketplace_patterns** — `knowledge_pack` → `knowledge-pack/task-marketplace-archetype-patterns`
2. **source_governance** — `tool` → `tool/source-record-governance-router`
3. **normalize_archetypes** — `tool` → `tool/task-marketplace-archetype-normalizer`
4. **entity_linking** — `tool` → `tool/entity-recognition-linker`
5. **dedupe** — `tool` → `tool/fuzzy-dedupe-clusterer`
6. **emit_index_records** — `tool` → `tool/index-record-emitter`
7. **review_routing** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/task-marketplace-archetype-patterns`

## Success criteria

- deterministic `$.outputs.normalized_objects` is_truthy `True`
- deterministic `$.outputs.review_tickets` is_truthy `True`

## Provenance

- Hub component: `pipeline/task-marketplace-archetype-intake` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
