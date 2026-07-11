---
license: CC-BY-4.0
tags:
- bulk-load
- cross_industry
- embedding
- evaluation
- experimental
- finance
- governance
- government
- healthcare
- huggingface
- legal
- media
- model-cards
- open-harness-hub
- pgvector
- postgres
- privacy
- promotion-scoring
- retrieval
- review-routing
- routing
- security
- serving
- software.devops
task_categories:
- sentence-similarity
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Specialized model card load plan patterns
---

# Specialized model card load plan patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/specialized-model-card-load-plan-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Load-plan patterns for preflighting, promotion-scoring, review-routing, and exporting specialized model-card row families into Postgres/pgvector bulk-load packages.

**Industries**: healthcare, finance, legal, software.devops, media, security, privacy, government, cross_industry
**Capabilities**: governance, evaluation, retrieval, routing, serving, embedding
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `load_plan_stage`
- `promotion_audit`
- `bulk_load_contract`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/specialized-model-card-load-plan-patterns/stages.jsonl` | jsonl | — |

## Provenance

- **sources**: scripts/factory/specialized_model_card_load_plan.py, dist/specialized-model-card-load-plan/seed/load-plan-manifest.json
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: public model metadata only; no model weights, private training data, PII, or source bodies copied

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/specialized-model-card-load-plan-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{specialized-model-card-load-plan-patterns_open_harness_hub,
  title  = {Specialized model card load plan patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/specialized-model-card-load-plan-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/specialized-model-card-load-plan-patterns`.
