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
- readiness
- retrieval
- software.devops
- vector-search
- worker-contract
task_categories:
- sentence-similarity
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Local embedding worker contract patterns
---

# Local embedding worker contract patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/local-embedding-worker-contract-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Checks for proving a local embedding worker can emit vector metadata rows that match planned completion stubs before production vector execution is enabled.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: embedding, retrieval, governance, evaluation
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `local_embedding_worker_contract_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/local-embedding-worker-contract-patterns/checks.jsonl` | jsonl | local_embedding_worker_contract_check |

## Provenance

- **sources**: Open Harness Hub local embedding worker contract, Open Harness Hub vector readiness audit, Open Harness Hub daily embedding execution planner
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: synthetic operational checks only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/local-embedding-worker-contract-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{local-embedding-worker-contract-patterns_open_harness_hub,
  title  = {Local embedding worker contract patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/local-embedding-worker-contract-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/local-embedding-worker-contract-patterns`.
