---
license: CC-BY-4.0
tags:
- ai
- components
- cross_industry
- dedupe
- entity-resolution
- evaluation
- experimental
- governance
- open-harness-hub
- postgres
- quality-index
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
pretty_name: Dedupe resolution patterns
---

# Dedupe resolution patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/dedupe-resolution-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Resolution actions, review boundaries, and load-order checks for clearing generated component candidates through fuzzy dedupe without approving content automatically.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: evaluation, governance, routing, verification
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `dedupe_resolution_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/dedupe-resolution-patterns/checks.jsonl` | jsonl | dedupe_resolution_check |

## Provenance

- **sources**: Open Harness Hub dedupe cluster schema, Open Harness Hub active component promotion plan
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: dedupe metadata only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/dedupe-resolution-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{dedupe-resolution-patterns_open_harness_hub,
  title  = {Dedupe resolution patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/dedupe-resolution-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/dedupe-resolution-patterns`.
