---
license: CC-BY-4.0
tags:
- ai
- component-candidates
- coverage
- cross_industry
- daily-factory
- experimental
- gap-analysis
- generation
- governance
- open-harness-hub
- planning
- retrieval
- showcase-pipelines
- software.devops
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Showcase gap component patterns
---

# Showcase gap component patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/showcase-gap-component-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Patterns for turning partial or missing showcase template coverage into targeted component candidate seeds for the next daily generation batch.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: generation, planning, retrieval, governance
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `showcase_gap_component_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/showcase-gap-component-patterns/checks.jsonl` | jsonl | showcase_gap_component_check |

## Provenance

- **sources**: Open Harness Hub showcase candidate coverage report, Open Harness Hub use-case seed row exporter
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: synthetic gap request rows only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/showcase-gap-component-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{showcase-gap-component-patterns_open_harness_hub,
  title  = {Showcase gap component patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/showcase-gap-component-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/showcase-gap-component-patterns`.
