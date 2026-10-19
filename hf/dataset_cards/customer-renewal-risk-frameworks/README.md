---
license: CC-BY-4.0
tags:
- customer-renewal-risk
- customer_success
- customer_success.renewal
- experimental
- open-harness-hub
- retrieval
- use-case-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Customer Renewal Risk frameworks
---

# Customer Renewal Risk frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/customer-renewal-risk-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite operational reference pack for customer renewal risk use cases.

**Industries**: customer_success, customer_success.renewal
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
| `data/customer-renewal-risk/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: renewal health score review, adoption and value realization analysis, executive sponsor mapping, customer escalation playbook
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/customer-renewal-risk-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{customer-renewal-risk-frameworks_open_harness_hub,
  title  = {Customer Renewal Risk frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/customer-renewal-risk-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/customer-renewal-risk-frameworks`.
