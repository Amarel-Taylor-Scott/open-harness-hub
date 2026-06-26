---
license: CC-BY-4.0
tags:
- ai
- cdc
- components
- cross_industry
- evaluation
- experimental
- governance
- index-delta
- open-harness-hub
- postgres
- promotion
- retrieval
- software.devops
- verification
- versioning
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Promotion CDC bridge patterns
---

# Promotion CDC bridge patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/promotion-cdc-bridge-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Checks for turning approved component promotion outputs into immutable component change events, index records, and review tickets.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, verification, retrieval, evaluation
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `promotion_cdc_bridge_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/promotion-cdc-bridge-patterns/checks.jsonl` | jsonl | promotion_cdc_bridge_check |

## Provenance

- **sources**: OpenHubForAI approved component promotion planner, OpenHubForAI component CDC planner
- **collected_through**: 2026-05-26
- **collected_by**: OpenHubForAI contributors
- **anonymization**: component lifecycle metadata only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/promotion-cdc-bridge-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{promotion-cdc-bridge-patterns_open_harness_hub,
  title  = {Promotion CDC bridge patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/promotion-cdc-bridge-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/promotion-cdc-bridge-patterns`.
