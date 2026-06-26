---
name: standards-regulatory-source-to-index
description: Turn prioritized standards and regulatory surfaces into governed, entity-linked,
  deduplicated, index-ready source and object records.
when_to_use: 'Pipeline kind: research_web.standards_regulatory_source_index_build.'
---

# Standards regulatory source to index

Prioritize standards and regulatory source surfaces, route governance, link entities, dedupe extracted objects, and emit source-backed index records for procedure and fact factories.

## Task

Turn prioritized standards and regulatory surfaces into governed, entity-linked, deduplicated, index-ready source and object records.

## Steps

1. **load_source_map** — `knowledge_pack` → `knowledge-pack/standards-regulatory-source-map`
2. **prioritize_sources** — `tool` → `tool/source-surface-prioritizer`
3. **governance_entity_dedupe_index** — `pipeline` → `pipeline/source-governance-entity-dedupe-index`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/standards-regulatory-source-map`
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- deterministic `$.outputs.ranked_sources` is_truthy `True`
- deterministic `$.outputs.index_records` is_truthy `True`

## Provenance

- Hub component: `pipeline/standards-regulatory-source-to-index` v0.1.0
- License: `MIT`
- Industry: ai, government, legal, healthcare.public_health, finance, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
