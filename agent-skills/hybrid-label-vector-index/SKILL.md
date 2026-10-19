---
name: hybrid-label-vector-index
description: Emit hybrid search records by labeling and dimensioning catalog/source
  objects, routing model-generated label work through a provider-neutral model router,
  and combining labels with vector/graph index records.
when_to_use: 'Pipeline kind: research_web.hybrid_label_vector_index.'
---

# Hybrid label vector index

Combine pgvector-style embeddings with hierarchical labels, schema.org-style labels, tenant custom labels, entity links, and model-generated dimensions for flexible hybrid search.

## Task

Emit hybrid search records by labeling and dimensioning catalog/source objects, routing model-generated label work through a provider-neutral model router, and combining labels with vector/graph index records.

## Steps

1. **load_label_taxonomy** — `knowledge_pack` → `knowledge-pack/hybrid-label-dimension-taxonomy`
2. **route_label_model** — `tool` → `tool/model-capability-router`
3. **assign_labels_dimensions** — `tool` → `tool/hierarchical-label-dimensioner`
4. **emit_hybrid_index_records** — `tool` → `tool/index-record-emitter`
5. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/hybrid-label-dimension-taxonomy`
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- deterministic `$.outputs.label_records` is_truthy `True`
- deterministic `$.outputs.dimension_records` is_truthy `True`

## Provenance

- Hub component: `pipeline/hybrid-label-vector-index` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
