---
license: CC-BY-4.0
tags:
- ai
- blocking
- cross_industry
- embedding-buckets
- entity-refs
- evaluation
- experimental
- governance
- government
- open-harness-hub
- pairwise-comparison
- resumable-workers
- retrieval
- routing
- software.devops
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Hybrid comparison blocking patterns
---

# Hybrid comparison blocking patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/hybrid-comparison-blocking-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Patterns for planning resumable object comparisons using normalized object fields plus labels, dimensions, entity refs, and embedding buckets.

**Industries**: ai, software.devops, government, cross_industry
**Capabilities**: retrieval, governance, evaluation, routing
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `comparison_block_pattern`
- `comparison_checkpoint_pattern`
- `hybrid_similarity_feature`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/hybrid-comparison-blocking-patterns/rows.jsonl` | jsonl | hybrid-comparison-blocking-pattern |

## Provenance

- **sources**: Open Harness Hub resumable object comparison planner, Open Harness Hub use-case seed entity and embedding bucket rows
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Synthetic comparison planning patterns only.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/hybrid-comparison-blocking-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{hybrid-comparison-blocking-patterns_open_harness_hub,
  title  = {Hybrid comparison blocking patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/hybrid-comparison-blocking-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/hybrid-comparison-blocking-patterns`.
