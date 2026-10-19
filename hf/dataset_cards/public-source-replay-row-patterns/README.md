---
license: CC-BY-4.0
tags:
- automotive
- classification
- construction
- cross_industry
- energy
- evaluation
- experimental
- extraction
- governance
- government
- jsonl
- manufacturing
- open-harness-hub
- pgvector
- preflight
- public-sources
- retrieval
- row-families
task_categories:
- text-classification
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Public source replay row patterns
---

# Public source replay row patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/public-source-replay-row-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Patterns for converting public-source replay records into canonical row-family JSONL shards for validation, preflight, and Postgres/pgvector bulk loading.

**Industries**: automotive, energy, manufacturing, construction, government, cross_industry
**Capabilities**: extraction, classification, retrieval, governance, evaluation
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `row_emission_pattern`
- `source_record`
- `normalized_object`
- `index_record`
- `review_ticket`

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/public-source-replay-row-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{public-source-replay-row-patterns_open_harness_hub,
  title  = {Public source replay row patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/public-source-replay-row-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/public-source-replay-row-patterns`.
