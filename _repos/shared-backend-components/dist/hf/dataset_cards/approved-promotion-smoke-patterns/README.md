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
- open-harness-hub
- postgres
- promotion
- retrieval
- review-gate
- smoke-test
- software.devops
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Approved promotion smoke patterns
---

# Approved promotion smoke patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/approved-promotion-smoke-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Synthetic approval-path checks that prove component promotion, component versioning, CDC, index projection, and review routing work together.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, verification, evaluation, retrieval
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `approved_promotion_smoke_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/approved-promotion-smoke-patterns/checks.jsonl` | jsonl | approved_promotion_smoke_check |

## Provenance

- **sources**: OpenHubForAI approved component promotion planner, OpenHubForAI promotion CDC bridge planner, OpenHubForAI component CDC planner
- **collected_through**: 2026-05-26
- **collected_by**: OpenHubForAI contributors
- **anonymization**: synthetic data only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/approved-promotion-smoke-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{approved-promotion-smoke-patterns_open_harness_hub,
  title  = {Approved promotion smoke patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/approved-promotion-smoke-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/approved-promotion-smoke-patterns`.
