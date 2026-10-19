---
license: CC-BY-4.0
tags:
- expansion-v3
- experimental
- immigration-case-intake
- legal.immigration
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
pretty_name: Immigration Case Intake frameworks
---

# Immigration Case Intake frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/immigration-case-intake-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for immigration case intake reviews, including evidence, escalation, and remediation controls.

**Industries**: legal.immigration
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
| `data/immigration-case-intake/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Immigration Case Intake control checklist, Immigration Case Intake evidence matrix, Immigration Case Intake escalation playbook, Immigration Case Intake remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/immigration-case-intake-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{immigration-case-intake-frameworks_open_harness_hub,
  title  = {Immigration Case Intake frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/immigration-case-intake-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/immigration-case-intake-frameworks`.
