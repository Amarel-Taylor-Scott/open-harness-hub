---
license: CC-BY-4.0
tags:
- ai
- candidate-primitives
- classification
- creative
- cross_industry
- dimension-records
- energy
- entity-refs
- experimental
- extraction
- finance
- governance
- healthcare
- hybrid-search
- label-records
- legal
- media
- object-embeddings
- open-harness-hub
- retrieval
- routing
- software.devops
- use-case-seeds
task_categories:
- text-classification
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Use case seed row patterns
---

# Use case seed row patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/use-case-seed-row-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Patterns for exporting broad use-case seeds into candidate primitive, entity ref, label, dimension, object embedding, review, dedupe, and index row families.

**Industries**: ai, software.devops, finance, legal, media, creative, energy, healthcare, cross_industry
**Capabilities**: classification, extraction, retrieval, routing, governance
**Modalities**: text, image, structured
**Freshness**: stable
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `use_case_seed_row_pattern`
- `label_assignment_mapping`
- `dimension_value_mapping`
- `entity_ref_mapping`
- `object_embedding_mapping`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/use-case-seed-row-patterns/rows.jsonl` | jsonl | use-case-seed-row-pattern |

## Provenance

- **sources**: Open Harness Hub cross-domain use-case seed surfaces, Open Harness Hub hybrid label and dimensional search architecture
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Synthetic row mappings only; insurance scope is excluded.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/use-case-seed-row-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{use-case-seed-row-patterns_open_harness_hub,
  title  = {Use case seed row patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/use-case-seed-row-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/use-case-seed-row-patterns`.
