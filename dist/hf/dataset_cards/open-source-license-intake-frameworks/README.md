---
license: CC-BY-4.0
tags:
- expansion-v3
- experimental
- legal.ip
- open-harness-hub
- open-source-license-intake
- retrieval
- software
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Open Source License Intake frameworks
---

# Open Source License Intake frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/open-source-license-intake-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for open source license intake reviews, including evidence, escalation, and remediation controls.

**Industries**: software, legal.ip
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
| `data/open-source-license-intake/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Open Source License Intake control checklist, Open Source License Intake evidence matrix, Open Source License Intake escalation playbook, Open Source License Intake remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/open-source-license-intake-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{open-source-license-intake-frameworks_open_harness_hub,
  title  = {Open Source License Intake frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/open-source-license-intake-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/open-source-license-intake-frameworks`.
