---
license: CC-BY-4.0
tags:
- ai
- blocking
- checkpointing
- cross_industry
- dedupe
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
pretty_name: Object comparison job patterns
---

# Object comparison job patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/object-comparison-job-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Seed patterns for blocked, leaf-sharded, checkpointed knowledge-object pairwise comparison jobs.

**Industries**: ai, software.devops, government, cross_industry
**Capabilities**: retrieval, governance, evaluation, routing
**Modalities**: text, structured
**Freshness**: volatile
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `comparison_job_pattern`
- `blocking_strategy`
- `leaf_checkpoint_contract`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/object-comparison-job-patterns/patterns.jsonl` | jsonl | object-comparison-job-pattern |

## Provenance

- **sources**: Open Harness Hub object factory scaling architecture
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Synthetic job-control patterns only; no raw object payloads.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/object-comparison-job-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{object-comparison-job-patterns_open_harness_hub,
  title  = {Object comparison job patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/object-comparison-job-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/object-comparison-job-patterns`.
