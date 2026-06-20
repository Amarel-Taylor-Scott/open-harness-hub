---
license: CC-BY-4.0
tags:
- ai
- canonical-store
- cross_industry
- evaluation
- experimental
- governance
- index-delta
- jsonl
- million-primitives
- open-harness-hub
- pgvector
- postgres
- retrieval
- serving
- software.devops
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Generated object storage patterns
---

# Generated object storage patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/generated-object-storage-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Storage patterns for moving generated source records, normalized objects, promotion decisions, index records, and index deltas from JSONL staging into canonical Postgres and pgvector tables.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, retrieval, serving, evaluation
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: hub

## Content types (leaf vocabulary)

- `storage_pattern`
- `postgres_loader_pattern`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/generated-object-storage-patterns/storage-patterns.jsonl` | jsonl | — |

## Provenance

- **sources**: Open Harness Hub primitive platform backend, Open Harness Hub Postgres schema, Open Harness Hub vector DB spec
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Architecture and synthetic storage patterns only; no PII or proprietary data.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/generated-object-storage-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{generated-object-storage-patterns_open_harness_hub,
  title  = {Generated object storage patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/generated-object-storage-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/generated-object-storage-patterns`.
