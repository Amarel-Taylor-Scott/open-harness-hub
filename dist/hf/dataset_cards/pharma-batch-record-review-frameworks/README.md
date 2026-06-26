---
license: CC-BY-4.0
tags:
- expansion-v7
- experimental
- open-harness-hub
- pharma-batch-record-review
- pharma.gxp
- pharma.manufacturing
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Pharma Batch Record Review frameworks
---

# Pharma Batch Record Review frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/pharma-batch-record-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for pharma batch record review workflows.

**Industries**: pharma.manufacturing, pharma.gxp
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
| `data/pharma-batch-record-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Pharma Batch Record Review control checklist, Pharma Batch Record Review evidence matrix, Pharma Batch Record Review escalation playbook, Pharma Batch Record Review benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/pharma-batch-record-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{pharma-batch-record-review-frameworks_open_harness_hub,
  title  = {Pharma Batch Record Review frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/pharma-batch-record-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/pharma-batch-record-review-frameworks`.
