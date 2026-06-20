---
license: CC-BY-4.0
tags:
- ai
- cross_industry
- daily-factory
- docker
- embedding
- embeddings
- evaluation
- experimental
- governance
- open-harness-hub
- pgvector
- postgres
- retrieval
- smoke-test
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
pretty_name: Local pgvector embedding smoke patterns
---

# Local pgvector embedding smoke patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/local-pgvector-embedding-smoke-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Checks for local Docker pgvector smoke plans that apply embedding load SQL, export committed counts, and rerun vector readiness audits.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: embedding, retrieval, governance, evaluation
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `local_pgvector_embedding_smoke_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/local-pgvector-embedding-smoke-patterns/checks.jsonl` | jsonl | local_pgvector_embedding_smoke_check |

## Provenance

- **sources**: Open Harness Hub local pgvector embedding smoke planner, Open Harness Hub pgvector embedding load planner, Open Harness Hub embedding committed load audit
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: synthetic operational checks only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/local-pgvector-embedding-smoke-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{local-pgvector-embedding-smoke-patterns_open_harness_hub,
  title  = {Local pgvector embedding smoke patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/local-pgvector-embedding-smoke-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/local-pgvector-embedding-smoke-patterns`.
