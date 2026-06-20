---
license: CC-BY-4.0
tags:
- ai
- cost-index
- cross_industry
- evaluation
- experimental
- facet-index
- governance
- index-delta
- million-primitives
- open-harness-hub
- promotion
- quality-index
- retrieval
- serving
- software.devops
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Promotion index delta patterns
---

# Promotion index delta patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/promotion-index-delta-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Seed promotion-decision index delta patterns for updating quality, facet, and cost indexes incrementally from high-volume candidate primitive scoring.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: evaluation, governance, retrieval, serving
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: hub

## Content types (leaf vocabulary)

- `promotion_decision`
- `index_delta_pattern`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/promotion-index-delta-patterns/promotion-decisions.jsonl` | jsonl | schemas/promotion-decision.schema.json |

## Provenance

- **sources**: Open Harness Hub candidate primitive promotion scoring, Open Harness Hub partitioned index delta architecture
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Synthetic promotion decisions only; no real PII or proprietary marketplace listing text.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/promotion-index-delta-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{promotion-index-delta-patterns_open_harness_hub,
  title  = {Promotion index delta patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/promotion-index-delta-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/promotion-index-delta-patterns`.
