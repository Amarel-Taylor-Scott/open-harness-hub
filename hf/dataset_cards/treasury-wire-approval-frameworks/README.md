---
license: CC-BY-4.0
tags:
- expansion-v5
- experimental
- finance.fraud
- finance.kyc
- open-harness-hub
- retrieval
- treasury-wire-approval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Treasury Wire Approval frameworks
---

# Treasury Wire Approval frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/treasury-wire-approval-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for treasury wire approval workflows.

**Industries**: finance.fraud, finance.kyc
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
| `data/treasury-wire-approval/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Treasury Wire Approval control checklist, Treasury Wire Approval evidence matrix, Treasury Wire Approval escalation playbook, Treasury Wire Approval benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/treasury-wire-approval-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{treasury-wire-approval-frameworks_open_harness_hub,
  title  = {Treasury Wire Approval frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/treasury-wire-approval-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/treasury-wire-approval-frameworks`.
