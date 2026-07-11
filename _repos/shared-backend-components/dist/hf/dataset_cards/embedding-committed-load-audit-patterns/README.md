---
license: CC-BY-4.0
tags:
- ai
- cross_industry
- daily-factory
- embedding
- embeddings
- evaluation
- experimental
- governance
- open-harness-hub
- pgvector
- postgres
- readiness-audit
- retrieval
- software.devops
- vector-search
task_categories:
- sentence-similarity
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Embedding committed load audit patterns
---

# Embedding committed load audit patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/embedding-committed-load-audit-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Checks for gating vector search readiness on planned, stored, load-planned, and committed Postgres embedding counts.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: embedding, retrieval, governance, evaluation
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `embedding_committed_load_audit_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/embedding-committed-load-audit-patterns/checks.jsonl` | jsonl | embedding_committed_load_audit_check |

## Provenance

- **sources**: OpenHubForAI embedding committed load audit, OpenHubForAI pgvector embedding load plan, OpenHubForAI object count report
- **collected_through**: 2026-05-26
- **collected_by**: OpenHubForAI contributors
- **anonymization**: synthetic operational checks only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/embedding-committed-load-audit-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{embedding-committed-load-audit-patterns_open_harness_hub,
  title  = {Embedding committed load audit patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/embedding-committed-load-audit-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/embedding-committed-load-audit-patterns`.
