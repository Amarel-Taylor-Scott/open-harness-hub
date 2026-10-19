---
name: signed-knowledge-object-to-index
description: Turn signed personal, organizational, government, and project knowledge
  objects into policy-aware indexed records for RAG and pipeline composition.
when_to_use: 'Pipeline kind: research_web.signed_knowledge_index_build.'
---

# Signed knowledge object to index

Verify publisher identity, ingest signed knowledge objects, enforce privacy and usage policy, and prepare records for keyword, vector, graph, and RAG retrieval.

## Task

Turn signed personal, organizational, government, and project knowledge objects into policy-aware indexed records for RAG and pipeline composition.

## Steps

1. **load_patterns** — `knowledge_pack` → `knowledge-pack/signed-knowledge-network-patterns`
2. **verify_publisher** — `tool` → `tool/publisher-identity-verifier`
3. **ingest_signed_objects** — `tool` → `tool/signed-knowledge-object-intake`
4. **normalize_records** — `tool` → `tool/search-result-normalizer`
5. **semantic_dedupe** — `tool` → `tool/embedding-index-search`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/signed-knowledge-network-patterns`
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- deterministic `$.outputs.keyword_index_records` is_truthy `True`
- deterministic `$.outputs.vector_index_records` is_truthy `True`

## Provenance

- Hub component: `pipeline/signed-knowledge-object-to-index` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
