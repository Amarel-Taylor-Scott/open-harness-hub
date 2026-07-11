---
license: CC-BY-4.0
tags:
- chemical-sds-review
- ehs.audit
- expansion-v4
- experimental
- manufacturing.qa
- open-harness-hub
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Chemical SDS Review frameworks
---

# Chemical SDS Review frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/chemical-sds-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for chemical sds review review, evidence, escalation, and benchmarking.

**Industries**: ehs.audit, manufacturing.qa
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
| `data/chemical-sds-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Chemical SDS Review control checklist, Chemical SDS Review evidence matrix, Chemical SDS Review escalation playbook, Chemical SDS Review benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/chemical-sds-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{chemical-sds-review-frameworks_open_harness_hub,
  title  = {Chemical SDS Review frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/chemical-sds-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/chemical-sds-review-frameworks`.
