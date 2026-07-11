---
license: CC-BY-4.0
tags:
- ai
- components
- cross_industry
- evaluation
- experimental
- governance
- index-records
- open-harness-hub
- postgres
- promotion
- quality
- review-gate
- routing
- software.devops
- verification
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Promotion decision load patterns
---

# Promotion decision load patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/promotion-decision-load-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Load-order, review-boundary, and index consistency checks for moving candidate promotion decisions into Postgres.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: evaluation, governance, routing, verification
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `promotion_decision_load_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/promotion-decision-load-patterns/checks.jsonl` | jsonl | promotion_decision_load_check |

## Provenance

- **sources**: OpenHubForAI promotion decision schema, OpenHubForAI candidate promotion scorer
- **collected_through**: 2026-05-26
- **collected_by**: OpenHubForAI contributors
- **anonymization**: promotion metadata only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/promotion-decision-load-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{promotion-decision-load-patterns_open_harness_hub,
  title  = {Promotion decision load patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/promotion-decision-load-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/promotion-decision-load-patterns`.
