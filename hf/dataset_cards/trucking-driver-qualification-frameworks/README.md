---
license: CC-BY-4.0
tags:
- expansion-v7
- experimental
- hr.performance
- open-harness-hub
- retrieval
- transportation.trucking
- trucking-driver-qualification
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Trucking Driver Qualification frameworks
---

# Trucking Driver Qualification frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/trucking-driver-qualification-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for trucking driver qualification workflows.

**Industries**: transportation.trucking, hr.performance
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
| `data/trucking-driver-qualification/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Trucking Driver Qualification control checklist, Trucking Driver Qualification evidence matrix, Trucking Driver Qualification escalation playbook, Trucking Driver Qualification benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/trucking-driver-qualification-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{trucking-driver-qualification-frameworks_open_harness_hub,
  title  = {Trucking Driver Qualification frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/trucking-driver-qualification-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/trucking-driver-qualification-frameworks`.
