---
license: CC-BY-4.0
tags:
- ai
- components
- cross_industry
- daily-factory
- embedding-execution
- evaluation
- experimental
- governance
- open-harness-hub
- planning
- postgres
- promotion
- retrieval
- review-gate
- software.devops
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Daily promotion readiness patterns
---

# Daily promotion readiness patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/daily-promotion-readiness-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Checks for separating candidate-table load readiness from active component promotion readiness after large daily production runs.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, evaluation, retrieval, planning
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `daily_promotion_readiness_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/daily-promotion-readiness-patterns/checks.jsonl` | jsonl | daily_promotion_readiness_check |

## Provenance

- **sources**: OpenHubForAI daily production runner, OpenHubForAI promotion planners, OpenHubForAI component-store load plan
- **collected_through**: 2026-05-26
- **collected_by**: OpenHubForAI contributors
- **anonymization**: synthetic operational checks only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/daily-promotion-readiness-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{daily-promotion-readiness-patterns_open_harness_hub,
  title  = {Daily promotion readiness patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/daily-promotion-readiness-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/daily-promotion-readiness-patterns`.
