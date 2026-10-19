---
license: CC-BY-4.0
tags:
- expansion-v7
- experimental
- finance.kyc
- open-harness-hub
- retrieval
- sanctions-ownership-chain
- trade.sanctions
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Sanctions Ownership Chain frameworks
---

# Sanctions Ownership Chain frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/sanctions-ownership-chain-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for sanctions ownership chain workflows.

**Industries**: trade.sanctions, finance.kyc
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
| `data/sanctions-ownership-chain/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Sanctions Ownership Chain control checklist, Sanctions Ownership Chain evidence matrix, Sanctions Ownership Chain escalation playbook, Sanctions Ownership Chain benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/sanctions-ownership-chain-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{sanctions-ownership-chain-frameworks_open_harness_hub,
  title  = {Sanctions Ownership Chain frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/sanctions-ownership-chain-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/sanctions-ownership-chain-frameworks`.
