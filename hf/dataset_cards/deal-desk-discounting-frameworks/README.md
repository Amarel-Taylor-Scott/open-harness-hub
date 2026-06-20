---
license: CC-BY-4.0
tags:
- deal-desk-discounting
- experimental
- legal.contract
- open-harness-hub
- retrieval
- sales_ops.discounting
- use-case-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Deal Desk Discounting frameworks
---

# Deal Desk Discounting frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/deal-desk-discounting-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite operational reference pack for deal desk discounting use cases.

**Industries**: sales_ops.discounting, legal.contract
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
| `data/deal-desk-discounting/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: discount approval matrix, margin and floor-price review, commercial exception governance, non-standard terms escalation
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/deal-desk-discounting-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{deal-desk-discounting-frameworks_open_harness_hub,
  title  = {Deal Desk Discounting frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/deal-desk-discounting-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/deal-desk-discounting-frameworks`.
