---
license: CC-BY-4.0
tags:
- bulk-load
- classification
- cross_industry
- embedding
- evaluation
- experimental
- extraction
- finance
- governance
- government
- healthcare
- huggingface
- jsonl
- legal
- media
- model-cards
- open-harness-hub
- pgvector
- privacy
- retrieval
- review-routing
- routing
- row-families
- security
- software.devops
task_categories:
- sentence-similarity
- text-classification
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Specialized model card row patterns
---

# Specialized model card row patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/specialized-model-card-row-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Canonical row-family patterns for converting specialized model-card scan jobs into loadable JSONL rows for Postgres, pgvector, hybrid search, dedupe, and review workflows.

**Industries**: healthcare, finance, legal, software.devops, media, security, privacy, government, cross_industry
**Capabilities**: extraction, classification, retrieval, evaluation, routing, governance, embedding
**Modalities**: structured, text, image
**Freshness**: stable
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `row_family_pattern`
- `object_factory_contract`
- `review_route`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/specialized-model-card-row-patterns/row-families.jsonl` | jsonl | — |

## Provenance

- **sources**: scripts/factory/specialized_model_card_rows.py, dist/specialized-model-card-rows/seed
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: public model metadata only; no model weights, private training data, PII, or source bodies copied

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/specialized-model-card-row-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{specialized-model-card-row-patterns_open_harness_hub,
  title  = {Specialized model card row patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/specialized-model-card-row-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/specialized-model-card-row-patterns`.
