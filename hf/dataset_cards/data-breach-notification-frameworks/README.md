---
license: CC-BY-4.0
tags:
- data-breach-notification
- expansion-v5
- experimental
- open-harness-hub
- privacy
- retrieval
- security.defensive
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Data Breach Notification frameworks
---

# Data Breach Notification frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/data-breach-notification-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for data breach notification workflows.

**Industries**: privacy, security.defensive
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
| `data/data-breach-notification/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Data Breach Notification control checklist, Data Breach Notification evidence matrix, Data Breach Notification escalation playbook, Data Breach Notification benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/data-breach-notification-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{data-breach-notification-frameworks_open_harness_hub,
  title  = {Data Breach Notification frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/data-breach-notification-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/data-breach-notification-frameworks`.
