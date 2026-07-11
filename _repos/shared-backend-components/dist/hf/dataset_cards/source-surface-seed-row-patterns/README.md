---
license: CC-BY-4.0
tags:
- automotive
- candidate-primitives
- classification
- construction
- cross_industry
- embedding-buckets
- energy
- entity-refs
- evaluation
- experimental
- extraction
- factory-rows
- governance
- government
- manufacturing
- open-harness-hub
- retrieval
- source-surfaces
task_categories:
- text-classification
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Source surface seed row patterns
---

# Source surface seed row patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/source-surface-seed-row-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Patterns for converting esoteric industry source-surface seeds into canonical factory row families for search, comparison, review, embedding backfill, and promotion.

**Industries**: automotive, energy, manufacturing, construction, government, cross_industry
**Capabilities**: extraction, classification, retrieval, governance, evaluation
**Modalities**: text, image, structured
**Freshness**: stable
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `source_surface_row_pattern`
- `candidate_primitive_mapping`
- `entity_ref_mapping`
- `object_embedding_mapping`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/source-surface-seed-row-patterns/rows.jsonl` | jsonl | source-surface-seed-row-pattern |

## Provenance

- **sources**: OpenHubForAI source surface seed row exporter, OpenHubForAI esoteric industry source surfaces
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: Synthetic source-surface row mappings only; no real PII or proprietary source material.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/source-surface-seed-row-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{source-surface-seed-row-patterns_open_harness_hub,
  title  = {Source surface seed row patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/source-surface-seed-row-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/source-surface-seed-row-patterns`.
