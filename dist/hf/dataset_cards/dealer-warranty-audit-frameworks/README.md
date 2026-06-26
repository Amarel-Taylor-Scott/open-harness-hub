---
license: CC-BY-4.0
tags:
- automotive.warranty
- dealer-warranty-audit
- expansion-v5
- experimental
- finance.fraud
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
pretty_name: Dealer Warranty Audit frameworks
---

# Dealer Warranty Audit frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/dealer-warranty-audit-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for dealer warranty audit workflows.

**Industries**: automotive.warranty, finance.fraud
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
| `data/dealer-warranty-audit/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Dealer Warranty Audit control checklist, Dealer Warranty Audit evidence matrix, Dealer Warranty Audit escalation playbook, Dealer Warranty Audit benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/dealer-warranty-audit-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{dealer-warranty-audit-frameworks_open_harness_hub,
  title  = {Dealer Warranty Audit frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/dealer-warranty-audit-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/dealer-warranty-audit-frameworks`.
