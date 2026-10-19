---
license: CC-BY-4.0
tags:
- ai
- components
- cross_industry
- daily-factory
- dedupe
- duplicate-collapse
- evaluation
- experimental
- governance
- id-stability
- load-audit
- open-harness-hub
- planning
- software.devops
- verification
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Duplicate collapse report patterns
---

# Duplicate collapse report patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/duplicate-collapse-report-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Checks for grouping staged row-family duplicate collapse by primary key, ID source, risk tier, and conflict status before Postgres load planning.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, verification, evaluation, planning
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `duplicate_collapse_report_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/duplicate-collapse-report-patterns/checks.jsonl` | jsonl | duplicate_collapse_report_check |

## Provenance

- **sources**: Open Harness Hub daily partition load audit, Open Harness Hub model-ops daily run, Open Harness Hub index coverage repair planner
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: synthetic operational checks only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/duplicate-collapse-report-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{duplicate-collapse-report-patterns_open_harness_hub,
  title  = {Duplicate collapse report patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/duplicate-collapse-report-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/duplicate-collapse-report-patterns`.
