---
license: CC-BY-4.0
tags:
- expansion-v3
- experimental
- finance
- finance.lending
- mortgage-underwriting-qc
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
pretty_name: Mortgage Underwriting QC frameworks
---

# Mortgage Underwriting QC frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/mortgage-underwriting-qc-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for mortgage underwriting qc reviews, including evidence, escalation, and remediation controls.

**Industries**: finance, finance.lending
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
| `data/mortgage-underwriting-qc/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Mortgage Underwriting QC control checklist, Mortgage Underwriting QC evidence matrix, Mortgage Underwriting QC escalation playbook, Mortgage Underwriting QC remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/mortgage-underwriting-qc-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{mortgage-underwriting-qc-frameworks_open_harness_hub,
  title  = {Mortgage Underwriting QC frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/mortgage-underwriting-qc-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/mortgage-underwriting-qc-frameworks`.
