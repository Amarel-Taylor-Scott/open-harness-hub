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
- load-plan
- open-harness-hub
- pgvector
- postgres
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
pretty_name: Pgvector embedding load patterns
---

# Pgvector embedding load patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/pgvector-embedding-load-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Checks for converting stored vector rows into reviewable pgvector object_embedding load SQL while preserving replay, dimensions, source text, and safety boundaries.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: embedding, retrieval, governance, evaluation
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `pgvector_embedding_load_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/pgvector-embedding-load-patterns/checks.jsonl` | jsonl | pgvector_embedding_load_check |

## Provenance

- **sources**: Open Harness Hub pgvector embedding load planner, Open Harness Hub local hash embedding worker, Open Harness Hub Postgres schema
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: synthetic operational checks only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/pgvector-embedding-load-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{pgvector-embedding-load-patterns_open_harness_hub,
  title  = {Pgvector embedding load patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/pgvector-embedding-load-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/pgvector-embedding-load-patterns`.
