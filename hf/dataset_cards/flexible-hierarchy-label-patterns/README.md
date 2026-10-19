---
license: CC-BY-4.0
tags:
- ai
- classification
- cross_industry
- dimensions
- energy
- experimental
- governance
- healthcare
- hierarchical-labels
- hybrid-search
- legal
- open-harness-hub
- retrieval
- routing
- software.devops
- taxonomy
- verticals
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Flexible hierarchy label patterns
---

# Flexible hierarchy label patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/flexible-hierarchy-label-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Patterns for representing new verticals, workflows, jurisdictions, and deployment contexts through hierarchical labels and dimensions instead of expanding core capability or modality vocabularies.

**Industries**: ai, software.devops, energy, healthcare, legal, cross_industry
**Capabilities**: classification, retrieval, routing, governance
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `hierarchical_label_pattern`
- `dimension_pattern`
- `taxonomy_extension_rule`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/flexible-hierarchy-label-patterns/patterns.jsonl` | jsonl | flexible-hierarchy-label-pattern |

## Provenance

- **sources**: Open Harness Hub hybrid label and dimensional search architecture
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Synthetic label examples only.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/flexible-hierarchy-label-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{flexible-hierarchy-label-patterns_open_harness_hub,
  title  = {Flexible hierarchy label patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/flexible-hierarchy-label-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/flexible-hierarchy-label-patterns`.
