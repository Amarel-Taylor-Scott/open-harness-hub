---
license: CC-BY-4.0
tags:
- ai
- component-version
- components
- cross_industry
- evaluation
- experimental
- governance
- open-harness-hub
- postgres
- promotion
- review-gate
- routing
- software.devops
- subcomponents
- verification
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Approved component promotion patterns
---

# Approved component promotion patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/approved-component-promotion-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Review-boundary, load-order, and state-transition checks for moving approved component candidates into active Postgres component rows.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: evaluation, governance, routing, verification
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `approved_component_promotion_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/approved-component-promotion-patterns/checks.jsonl` | jsonl | approved_component_promotion_check |

## Provenance

- **sources**: OpenHubForAI Postgres component schema, OpenHubForAI promotion decision load plan
- **collected_through**: 2026-05-26
- **collected_by**: OpenHubForAI contributors
- **anonymization**: promotion metadata only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/approved-component-promotion-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{approved-component-promotion-patterns_open_harness_hub,
  title  = {Approved component promotion patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/approved-component-promotion-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/approved-component-promotion-patterns`.
