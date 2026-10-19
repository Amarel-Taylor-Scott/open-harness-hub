---
license: CC-BY-4.0
tags:
- construction-change-order
- construction.permitting
- construction.safety
- expansion-v7
- experimental
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
pretty_name: Construction Change Order frameworks
---

# Construction Change Order frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/construction-change-order-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for construction change order workflows.

**Industries**: construction.permitting, construction.safety
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
| `data/construction-change-order/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Construction Change Order control checklist, Construction Change Order evidence matrix, Construction Change Order escalation playbook, Construction Change Order benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/construction-change-order-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{construction-change-order-frameworks_open_harness_hub,
  title  = {Construction Change Order frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/construction-change-order-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/construction-change-order-frameworks`.
