---
license: CC-BY-4.0
tags:
- aircraft-maintenance-deferral
- aviation.maintenance
- expansion-v6
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
pretty_name: Aircraft Maintenance Deferral frameworks
---

# Aircraft Maintenance Deferral frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/aircraft-maintenance-deferral-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for aircraft maintenance deferral workflows.

**Industries**: aviation.maintenance
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
| `data/aircraft-maintenance-deferral/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Aircraft Maintenance Deferral control checklist, Aircraft Maintenance Deferral evidence matrix, Aircraft Maintenance Deferral escalation playbook, Aircraft Maintenance Deferral benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/aircraft-maintenance-deferral-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{aircraft-maintenance-deferral-frameworks_open_harness_hub,
  title  = {Aircraft Maintenance Deferral frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/aircraft-maintenance-deferral-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/aircraft-maintenance-deferral-frameworks`.
