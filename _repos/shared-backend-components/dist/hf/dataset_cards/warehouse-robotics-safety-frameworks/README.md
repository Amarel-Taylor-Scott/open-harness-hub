---
license: CC-BY-4.0
tags:
- expansion-v5
- experimental
- logistics.warehouse
- manufacturing.qa
- open-harness-hub
- retrieval
- verification
- warehouse-robotics-safety
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Warehouse Robotics Safety frameworks
---

# Warehouse Robotics Safety frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/warehouse-robotics-safety-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for warehouse robotics safety workflows.

**Industries**: logistics.warehouse, manufacturing.qa
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
| `data/warehouse-robotics-safety/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Warehouse Robotics Safety control checklist, Warehouse Robotics Safety evidence matrix, Warehouse Robotics Safety escalation playbook, Warehouse Robotics Safety benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/warehouse-robotics-safety-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{warehouse-robotics-safety-frameworks_open_harness_hub,
  title  = {Warehouse Robotics Safety frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/warehouse-robotics-safety-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/warehouse-robotics-safety-frameworks`.
