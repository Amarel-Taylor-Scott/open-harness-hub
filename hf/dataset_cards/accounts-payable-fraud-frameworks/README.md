---
license: CC-BY-4.0
tags:
- accounts-payable-fraud
- expansion-v5
- experimental
- finance.fraud
- open-harness-hub
- procurement.vendor_risk
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Accounts Payable Fraud frameworks
---

# Accounts Payable Fraud frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/accounts-payable-fraud-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for accounts payable fraud workflows.

**Industries**: finance.fraud, procurement.vendor_risk
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
| `data/accounts-payable-fraud/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Accounts Payable Fraud control checklist, Accounts Payable Fraud evidence matrix, Accounts Payable Fraud escalation playbook, Accounts Payable Fraud benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/accounts-payable-fraud-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{accounts-payable-fraud-frameworks_open_harness_hub,
  title  = {Accounts Payable Fraud frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/accounts-payable-fraud-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/accounts-payable-fraud-frameworks`.
