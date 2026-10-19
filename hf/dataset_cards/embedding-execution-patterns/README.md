---
license: CC-BY-4.0
tags:
- ai
- audit
- batching
- cost-estimation
- cross_industry
- embedding
- embeddings
- evaluation
- experimental
- governance
- open-harness-hub
- pgvector
- retrieval
- serving
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
pretty_name: Embedding execution patterns
---

# Embedding execution patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/embedding-execution-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Provider-neutral embedding execution profiles and audit requirements for turning staged object_embedding rows into batch plans, completion records, and verified vector-search readiness.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: retrieval, embedding, governance, evaluation, serving
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `embedding_execution_profile`
- `embedding_audit_requirement`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/embedding-execution-patterns/profiles.jsonl` | jsonl | embedding_execution_profile |

## Provenance

- **sources**: Open Harness Hub object_embedding schema and pgvector storage plan
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: profile metadata only; no source text or PII

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/embedding-execution-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{embedding-execution-patterns_open_harness_hub,
  title  = {Embedding execution patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/embedding-execution-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/embedding-execution-patterns`.
