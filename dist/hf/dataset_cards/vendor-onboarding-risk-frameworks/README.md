---
license: CC-BY-4.0
tags:
- compliance
- experimental
- open-harness-hub
- procurement.vendor_risk
- retrieval
- use-case-expansion
- vendor-onboarding-risk
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Vendor Onboarding Risk frameworks
---

# Vendor Onboarding Risk frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/vendor-onboarding-risk-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite operational reference pack for vendor onboarding risk use cases.

**Industries**: procurement.vendor_risk, compliance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`

## Files

| path | format | schema |
|---|---|---|
| `data/vendor-onboarding-risk/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: third-party risk tiering, sanctions and adverse media screening, security questionnaire review, insurance and financial viability checks
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/vendor-onboarding-risk-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{vendor-onboarding-risk-frameworks_open_harness_hub,
  title  = {Vendor Onboarding Risk frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/vendor-onboarding-risk-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/vendor-onboarding-risk-frameworks`.
