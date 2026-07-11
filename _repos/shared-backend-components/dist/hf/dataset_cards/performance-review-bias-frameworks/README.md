---
license: CC-BY-4.0
tags:
- expansion-v7
- experimental
- hr.compensation
- hr.performance
- open-harness-hub
- performance-review-bias
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Performance Review Bias frameworks
---

# Performance Review Bias frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/performance-review-bias-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for performance review bias workflows.

**Industries**: hr.performance, hr.compensation
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`
- `evidence_matrix`
- `benchmark_context`

## Files

| path | format | schema |
|---|---|---|
| `data/performance-review-bias/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Performance Review Bias control checklist, Performance Review Bias evidence matrix, Performance Review Bias escalation playbook, Performance Review Bias benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/performance-review-bias-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{performance-review-bias-frameworks_open_harness_hub,
  title  = {Performance Review Bias frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/performance-review-bias-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/performance-review-bias-frameworks`.
