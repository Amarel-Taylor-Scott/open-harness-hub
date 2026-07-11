---
license: CC-BY-4.0
tags:
- ai
- cross_industry
- dedupe
- entity-resolution
- evaluation
- experimental
- finance.aml
- governance
- labels
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
pretty_name: Canonical factory row patterns
---

# Canonical factory row patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/canonical-factory-row-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Synthetic generated-object row patterns covering provenance, normalized objects, dedupe, entity links, review tickets, labels, dimensions, embeddings, and index records for Postgres-scale factories.

**Industries**: ai, software.devops, finance.aml, cross_industry
**Capabilities**: governance, retrieval, evaluation, serving
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `factory_row_fixture`
- `relationship_preflight_fixture`
- `bulk_load_fixture`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/canonical-factory-row-patterns/source-records.jsonl` | jsonl | source-record |
| `catalog/knowledge-packs/data/canonical-factory-row-patterns/normalized-objects.jsonl` | jsonl | normalized-object |
| `catalog/knowledge-packs/data/canonical-factory-row-patterns/dedupe-clusters.jsonl` | jsonl | dedupe-cluster |
| `catalog/knowledge-packs/data/canonical-factory-row-patterns/canonical-entities.jsonl` | jsonl | canonical-entity |
| `catalog/knowledge-packs/data/canonical-factory-row-patterns/object-entity-refs.jsonl` | jsonl | object-entity-ref |
| `catalog/knowledge-packs/data/canonical-factory-row-patterns/review-tickets.jsonl` | jsonl | review-ticket |
| `catalog/knowledge-packs/data/canonical-factory-row-patterns/label-assignments.jsonl` | jsonl | label-assignment |
| `catalog/knowledge-packs/data/canonical-factory-row-patterns/dimension-values.jsonl` | jsonl | dimension-value |
| `catalog/knowledge-packs/data/canonical-factory-row-patterns/object-embeddings.jsonl` | jsonl | object-embedding |
| `catalog/knowledge-packs/data/canonical-factory-row-patterns/index-records.jsonl` | jsonl | index-record |

## Provenance

- **sources**: Synthetic OpenHubForAI fixtures, OpenHubForAI canonical Postgres schema
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: Synthetic data only; no personal data, secrets, or proprietary source records.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/canonical-factory-row-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{canonical-factory-row-patterns_open_harness_hub,
  title  = {Canonical factory row patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/canonical-factory-row-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/canonical-factory-row-patterns`.
