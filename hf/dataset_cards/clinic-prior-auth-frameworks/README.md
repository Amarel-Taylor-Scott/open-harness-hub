---
license: CC-BY-4.0
tags:
- clinic-prior-auth
- expansion-v3
- experimental
- healthcare.clinical
- healthcare.payer
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
pretty_name: Clinic Prior Authorization frameworks
---

# Clinic Prior Authorization frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/clinic-prior-auth-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for clinic prior authorization reviews, including evidence, escalation, and remediation controls.

**Industries**: healthcare.clinical, healthcare.payer
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
| `data/clinic-prior-auth/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Clinic Prior Authorization control checklist, Clinic Prior Authorization evidence matrix, Clinic Prior Authorization escalation playbook, Clinic Prior Authorization remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/clinic-prior-auth-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{clinic-prior-auth-frameworks_open_harness_hub,
  title  = {Clinic Prior Authorization frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/clinic-prior-auth-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/clinic-prior-auth-frameworks`.
