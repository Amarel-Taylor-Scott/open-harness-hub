---
license: CC-BY-4.0
tags:
- bank-complaints-udaap
- compliance
- expansion-v3
- experimental
- finance
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
pretty_name: Bank Complaints UDAAP frameworks
---

# Bank Complaints UDAAP frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/bank-complaints-udaap-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for bank complaints udaap reviews, including evidence, escalation, and remediation controls.

**Industries**: finance, compliance
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
| `data/bank-complaints-udaap/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Bank Complaints UDAAP control checklist, Bank Complaints UDAAP evidence matrix, Bank Complaints UDAAP escalation playbook, Bank Complaints UDAAP remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/bank-complaints-udaap-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{bank-complaints-udaap-frameworks_open_harness_hub,
  title  = {Bank Complaints UDAAP frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/bank-complaints-udaap-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/bank-complaints-udaap-frameworks`.
