---
license: CC-BY-4.0
tags:
- construction
- cross_industry
- energy
- evaluation
- execution-summary
- experimental
- finance
- governance
- government
- healthcare
- load-readiness
- media
- multi-day-runs
- object-counts
- open-harness-hub
- retrieval
- routing
- serving
- software
- source-surfaces
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Source surface execution summary patterns
---

# Source surface execution summary patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/source-surface-execution-summary-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Metric contracts for monitoring source-surface partition runs from planned partitions through replay, generated rows, promotion decisions, review tickets, and bulk-load readiness.

**Industries**: government, software, media, construction, energy, finance, healthcare, cross_industry
**Capabilities**: governance, evaluation, retrieval, routing, serving
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `execution_summary_metric`
- `object_factory_progress_metric`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/source-surface-execution-summary-patterns/metrics.jsonl` | jsonl | execution_summary_metric |

## Provenance

- **sources**: OpenHubForAI source-surface partition, replay, row-emission, and load-plan outputs
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: metric contracts only; no raw source bodies or PII

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/source-surface-execution-summary-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{source-surface-execution-summary-patterns_open_harness_hub,
  title  = {Source surface execution summary patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/source-surface-execution-summary-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/source-surface-execution-summary-patterns`.
