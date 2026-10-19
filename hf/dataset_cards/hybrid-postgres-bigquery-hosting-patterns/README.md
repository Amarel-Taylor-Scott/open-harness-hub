---
license: CC-BY-4.0
tags:
- ai
- bigquery
- cross_industry
- evaluation
- experimental
- governance
- low-cost-hosting
- object-storage
- open-harness-hub
- pgvector
- postgres
- retrieval
- serving
- software.devops
- vector-search
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Hybrid Postgres BigQuery hosting patterns
---

# Hybrid Postgres BigQuery hosting patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/hybrid-postgres-bigquery-hosting-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Low-cost hosting patterns for keeping Open Harness Hub product state in Postgres/pgvector while using object storage and BigQuery for cold shards, vector analytics, cost traces, ranking, and trajectory-fragment cache analysis.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, retrieval, serving, evaluation
**Modalities**: text, structured, tabular
**Freshness**: dated
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `hosting_pattern`
- `cost_control_pattern`
- `warehouse_tier_pattern`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/hybrid-postgres-bigquery-hosting-patterns/patterns.jsonl` | jsonl | hybrid-hosting-pattern |

## Provenance

- **sources**: https://docs.cloud.google.com/bigquery/docs/vector-index, https://cloud.google.com/bigquery/docs/vector-search-intro, https://docs.cloud.google.com/bigquery/docs/best-practices-costs, https://docs.cloud.google.com/sql/docs/postgres/ai-overview
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: No personal data; architecture and cost-control patterns only.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/hybrid-postgres-bigquery-hosting-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{hybrid-postgres-bigquery-hosting-patterns_open_harness_hub,
  title  = {Hybrid Postgres BigQuery hosting patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/hybrid-postgres-bigquery-hosting-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/hybrid-postgres-bigquery-hosting-patterns`.
