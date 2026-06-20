---
license: CC-BY-4.0
tags:
- experimental
- open-harness-hub
- procurement
- procurement-bid-review
- procurement.sourcing
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
pretty_name: Procurement Bid Review frameworks
---

# Procurement Bid Review frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/procurement-bid-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite operational reference pack for procurement bid review use cases.

**Industries**: procurement, procurement.sourcing
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
| `data/procurement-bid-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: competitive bidding controls, evaluation scoring matrix, conflict-of-interest disclosure, single-source justification review
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/procurement-bid-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{procurement-bid-review-frameworks_open_harness_hub,
  title  = {Procurement Bid Review frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/procurement-bid-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/procurement-bid-review-frameworks`.
