---
license: CC-BY-4.0
tags:
- ai
- components
- cross_industry
- database-first
- experimental
- governance
- object-factory
- open-harness-hub
- pgvector
- postgres
- retrieval
- serving
- software.devops
- subcomponents
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Database component store patterns
---

# Database component store patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/database-component-store-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Patterns for storing active components and subcomponents in Postgres first, while treating repository files and JSONL as seed, staging, and export formats.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, retrieval, serving, verification
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `component_store_stage`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/database-component-store-patterns/stages.jsonl` | jsonl | component_store_stage |

## Provenance

- **sources**: Open Harness Hub north star platform architecture, Open Harness Hub Postgres schema
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: schema and process metadata only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/database-component-store-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{database-component-store-patterns_open_harness_hub,
  title  = {Database component store patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/database-component-store-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/database-component-store-patterns`.
