---
license: CC-BY-4.0
tags:
- contract-obligation-tracking
- expansion-v5
- experimental
- legal.contract
- open-harness-hub
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
pretty_name: Contract Obligation Tracking frameworks
---

# Contract Obligation Tracking frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/contract-obligation-tracking-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for contract obligation tracking workflows.

**Industries**: legal.contract, procurement.contracting
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
| `data/contract-obligation-tracking/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Contract Obligation Tracking control checklist, Contract Obligation Tracking evidence matrix, Contract Obligation Tracking escalation playbook, Contract Obligation Tracking benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/contract-obligation-tracking-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{contract-obligation-tracking-frameworks_open_harness_hub,
  title  = {Contract Obligation Tracking frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/contract-obligation-tracking-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/contract-obligation-tracking-frameworks`.
