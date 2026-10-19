---
license: CC-BY-4.0
tags:
- expansion-v6
- experimental
- healthcare.clinical
- hospital-discharge-safety
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
pretty_name: Hospital Discharge Safety frameworks
---

# Hospital Discharge Safety frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/hospital-discharge-safety-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for hospital discharge safety workflows.

**Industries**: healthcare.clinical
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
| `data/hospital-discharge-safety/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Hospital Discharge Safety control checklist, Hospital Discharge Safety evidence matrix, Hospital Discharge Safety escalation playbook, Hospital Discharge Safety benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/hospital-discharge-safety-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{hospital-discharge-safety-frameworks_open_harness_hub,
  title  = {Hospital Discharge Safety frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/hospital-discharge-safety-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/hospital-discharge-safety-frameworks`.
