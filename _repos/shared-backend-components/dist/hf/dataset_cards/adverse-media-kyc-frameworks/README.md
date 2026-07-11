---
license: CC-BY-4.0
tags:
- adverse-media-kyc
- expansion-v3
- experimental
- finance.aml
- finance.kyc
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
pretty_name: Adverse Media KYC frameworks
---

# Adverse Media KYC frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/adverse-media-kyc-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for adverse media kyc reviews, including evidence, escalation, and remediation controls.

**Industries**: finance.kyc, finance.aml
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
| `data/adverse-media-kyc/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Adverse Media KYC control checklist, Adverse Media KYC evidence matrix, Adverse Media KYC escalation playbook, Adverse Media KYC remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/adverse-media-kyc-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{adverse-media-kyc-frameworks_open_harness_hub,
  title  = {Adverse Media KYC frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/adverse-media-kyc-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/adverse-media-kyc-frameworks`.
