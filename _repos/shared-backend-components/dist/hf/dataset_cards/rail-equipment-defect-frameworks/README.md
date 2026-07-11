---
license: CC-BY-4.0
tags:
- expansion-v3
- experimental
- open-harness-hub
- rail-equipment-defect
- retrieval
- transportation.rail
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Rail Equipment Defect frameworks
---

# Rail Equipment Defect frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/rail-equipment-defect-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for rail equipment defect reviews, including evidence, escalation, and remediation controls.

**Industries**: transportation.rail
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`
- `evidence_matrix`

## Files

| path | format | schema |
|---|---|---|
| `data/rail-equipment-defect/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Rail Equipment Defect control checklist, Rail Equipment Defect evidence matrix, Rail Equipment Defect escalation playbook, Rail Equipment Defect remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/rail-equipment-defect-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{rail-equipment-defect-frameworks_open_harness_hub,
  title  = {Rail Equipment Defect frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/rail-equipment-defect-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/rail-equipment-defect-frameworks`.
