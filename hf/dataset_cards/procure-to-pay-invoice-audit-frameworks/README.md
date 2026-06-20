---
license: CC-BY-4.0
tags:
- expansion-v5
- experimental
- finance.fraud
- open-harness-hub
- procure-to-pay-invoice-audit
- procurement.contracting
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Procure To Pay Invoice Audit frameworks
---

# Procure To Pay Invoice Audit frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/procure-to-pay-invoice-audit-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for procure to pay invoice audit workflows.

**Industries**: procurement.contracting, finance.fraud
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`
- `evidence_matrix`
- `benchmark_context`

## Files

| path | format | schema |
|---|---|---|
| `data/procure-to-pay-invoice-audit/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Procure To Pay Invoice Audit control checklist, Procure To Pay Invoice Audit evidence matrix, Procure To Pay Invoice Audit escalation playbook, Procure To Pay Invoice Audit benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/procure-to-pay-invoice-audit-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{procure-to-pay-invoice-audit-frameworks_open_harness_hub,
  title  = {Procure To Pay Invoice Audit frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/procure-to-pay-invoice-audit-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/procure-to-pay-invoice-audit-frameworks`.
