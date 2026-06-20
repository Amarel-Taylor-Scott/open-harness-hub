---
license: CC-BY-4.0
tags:
- ai
- bulk-load
- components
- cross_industry
- experimental
- open-harness-hub
- pgvector
- pipeline-template
- planning
- postgres
- review-gate
- routing
- serving
- software.devops
- verification
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Component template load patterns
---

# Component template load patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/component-template-load-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Load-order, review, reference, and search-index checks for moving reusable pipeline templates into Postgres template tables.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: planning, routing, serving, verification
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `component_template_load_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/component-template-load-patterns/checks.jsonl` | jsonl | component_template_load_check |

## Provenance

- **sources**: Open Harness Hub component pipeline template expander, Open Harness Hub Postgres schema
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: template metadata only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/component-template-load-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{component-template-load-patterns_open_harness_hub,
  title  = {Component template load patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/component-template-load-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/component-template-load-patterns`.
