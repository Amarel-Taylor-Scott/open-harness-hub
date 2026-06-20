---
name: primitive-source-surface-to-index
description: Convert routine source-surface scans and verified-source submissions
  into indexed candidate primitives for search and blueprint generation.
when_to_use: 'Pipeline kind: research_web.primitive_index_build.'
---

# Primitive source surface to index

Scan source surfaces, normalize candidate primitives, apply verified-source rules, and prepare records for keyword, vector, graph, and model-polished search.

## Task

Convert routine source-surface scans and verified-source submissions into indexed candidate primitives for search and blueprint generation.

## Steps

1. **load_source_surfaces** — `knowledge_pack` → `knowledge-pack/primitive-source-surface-map`
2. **scan_surfaces** — `tool` → `tool/primitive-source-surface-scanner`
3. **verified_source_intake** — `tool` → `tool/verified-source-publisher-intake`
4. **normalize_records** — `tool` → `tool/search-result-normalizer`
5. **score_gap_signals** — `tool` → `tool/capability-gap-signal-scorer`
6. **semantic_catalog_dedupe** — `tool` → `tool/embedding-index-search`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/primitive-source-surface-map`, `knowledge-pack/capability-gap-discovery-patterns`
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- deterministic `$.outputs.candidate_primitives` is_truthy `True`
- deterministic `$.outputs.keyword_index_records` is_truthy `True`

## Provenance

- Hub component: `pipeline/primitive-source-surface-to-index` v0.1.0
- License: `MIT`
- Industry: ai, cross_industry
- Full source manifest: see `references/manifest.yaml`
