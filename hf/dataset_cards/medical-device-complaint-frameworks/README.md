---
license: CC-BY-4.0
tags:
- expansion-v3
- experimental
- healthcare
- medical-device-complaint
- open-harness-hub
- pharma.gxp
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Medical Device Complaint frameworks
---

# Medical Device Complaint frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/medical-device-complaint-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for medical device complaint reviews, including evidence, escalation, and remediation controls.

**Industries**: healthcare, pharma.gxp
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
| `data/medical-device-complaint/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Medical Device Complaint control checklist, Medical Device Complaint evidence matrix, Medical Device Complaint escalation playbook, Medical Device Complaint remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/medical-device-complaint-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{medical-device-complaint-frameworks_open_harness_hub,
  title  = {Medical Device Complaint frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/medical-device-complaint-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/medical-device-complaint-frameworks`.
