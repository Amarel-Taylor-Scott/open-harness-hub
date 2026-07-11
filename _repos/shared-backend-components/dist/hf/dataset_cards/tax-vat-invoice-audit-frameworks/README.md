---
license: CC-BY-4.0
tags:
- expansion-v6
- experimental
- finance.fraud
- open-harness-hub
- retrieval
- tax-vat-invoice-audit
- tax.indirect
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Tax VAT Invoice Audit frameworks
---

# Tax VAT Invoice Audit frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/tax-vat-invoice-audit-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for tax vat invoice audit workflows.

**Industries**: tax.indirect, finance.fraud
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
| `data/tax-vat-invoice-audit/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Tax VAT Invoice Audit control checklist, Tax VAT Invoice Audit evidence matrix, Tax VAT Invoice Audit escalation playbook, Tax VAT Invoice Audit benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/tax-vat-invoice-audit-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{tax-vat-invoice-audit-frameworks_open_harness_hub,
  title  = {Tax VAT Invoice Audit frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/tax-vat-invoice-audit-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/tax-vat-invoice-audit-frameworks`.
