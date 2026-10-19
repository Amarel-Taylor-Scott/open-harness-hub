---
license: CC-BY-4.0
tags:
- ai
- component-templates
- cross_industry
- daily-factory
- evaluation
- experimental
- governance
- open-harness-hub
- planning
- postgres
- review-gate
- routing
- showcase-pipelines
- software.devops
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Daily showcase pipeline patterns
---

# Daily showcase pipeline patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/daily-showcase-pipeline-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Scenario seeds and checks for generating 5 to 25 review-ready, database-backed showcase pipeline templates per day.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: planning, routing, evaluation, governance
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `daily_showcase_pipeline_scenario`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/daily-showcase-pipeline-patterns/showcase-scenarios.jsonl` | jsonl | daily_showcase_pipeline_scenario |

## Provenance

- **sources**: Open Harness Hub daily production target, Open Harness Hub component template load planner, Open Harness Hub user-provided showcase use-case families
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: synthetic scenario seeds only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/daily-showcase-pipeline-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{daily-showcase-pipeline-patterns_open_harness_hub,
  title  = {Daily showcase pipeline patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/daily-showcase-pipeline-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/daily-showcase-pipeline-patterns`.
