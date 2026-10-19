---
license: CC-BY-4.0
tags:
- automotive
- checkpoints
- construction
- cross_industry
- energy
- evaluation
- experimental
- governance
- government
- job-replay
- manufacturing
- object-factory
- open-harness-hub
- partition-manifests
- public-sources
- retrieval
- routing
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Public source job replay patterns
---

# Public source job replay patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/public-source-job-replay-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Patterns for replaying queued public-source scan jobs into run records, checkpoints, output pointers, and partition manifests without storing source bodies.

**Industries**: automotive, energy, manufacturing, construction, government, cross_industry
**Capabilities**: routing, governance, evaluation, retrieval
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `worker_replay_pattern`
- `job_run_record`
- `checkpoint`
- `partition_manifest`

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/public-source-job-replay-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{public-source-job-replay-patterns_open_harness_hub,
  title  = {Public source job replay patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/public-source-job-replay-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/public-source-job-replay-patterns`.
