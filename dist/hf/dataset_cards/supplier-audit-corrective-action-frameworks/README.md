---
license: CC-BY-4.0
tags:
- expansion-v7
- experimental
- open-harness-hub
- procurement.vendor_risk
- retrieval
- supplier-audit-corrective-action
- supply_chain.audit
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Supplier Audit Corrective Action frameworks
---

# Supplier Audit Corrective Action frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/supplier-audit-corrective-action-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for supplier audit corrective action workflows.

**Industries**: supply_chain.audit, procurement.vendor_risk
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
| `data/supplier-audit-corrective-action/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Supplier Audit Corrective Action control checklist, Supplier Audit Corrective Action evidence matrix, Supplier Audit Corrective Action escalation playbook, Supplier Audit Corrective Action benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/supplier-audit-corrective-action-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{supplier-audit-corrective-action-frameworks_open_harness_hub,
  title  = {Supplier Audit Corrective Action frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/supplier-audit-corrective-action-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/supplier-audit-corrective-action-frameworks`.
