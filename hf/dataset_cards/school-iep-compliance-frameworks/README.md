---
license: CC-BY-4.0
tags:
- education.k12
- expansion-v3
- experimental
- open-harness-hub
- retrieval
- school-iep-compliance
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: School IEP Compliance frameworks
---

# School IEP Compliance frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/school-iep-compliance-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for school iep compliance reviews, including evidence, escalation, and remediation controls.

**Industries**: education.k12
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
| `data/school-iep-compliance/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: School IEP Compliance control checklist, School IEP Compliance evidence matrix, School IEP Compliance escalation playbook, School IEP Compliance remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/school-iep-compliance-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{school-iep-compliance-frameworks_open_harness_hub,
  title  = {School IEP Compliance frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/school-iep-compliance-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/school-iep-compliance-frameworks`.
