---
license: CC-BY-4.0
tags:
- disaster-assistance
- environmental.water
- evaluation
- experimental
- food-quality
- food.safety
- food_safety
- governance
- government.benefits
- humanitarian.disaster
- model-routing
- multimodal
- open-harness-hub
- public-service
- retrieval
- verification
- water-quality
- water_utility.sdwa
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Multimodal public service patterns
---

# Multimodal public service patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/multimodal-public-service-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reusable multimodal harness patterns for disaster assistance, water quality, and food quality workflows that require model routing, official-source retrieval, evidence normalization, and human review.

**Industries**: humanitarian.disaster, government.benefits, environmental.water, water_utility.sdwa, food.safety, food_safety
**Capabilities**: governance, retrieval, verification, evaluation
**Modalities**: text, image, structured, tabular, spatial, timeseries, multimodal
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `multimodal_harness_pattern`
- `public_service_workflow_pattern`
- `model_routing_pattern`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/multimodal-public-service-patterns/patterns.jsonl` | jsonl | multimodal-public-service-pattern |

## Provenance

- **sources**: OpenHubForAI public-service and quality workflow catalog, User-requested multimodal harness expansion from 2026-05-25
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: No personal data; pattern summaries and synthetic examples only.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/multimodal-public-service-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{multimodal-public-service-patterns_open_harness_hub,
  title  = {Multimodal public service patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/multimodal-public-service-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/multimodal-public-service-patterns`.
