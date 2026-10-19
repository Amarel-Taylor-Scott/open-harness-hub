---
license: CC-BY-4.0
tags:
- experimental
- open-harness-hub
- prd-readiness-review
- product_management
- product_management.prd
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
pretty_name: PRD Readiness Review frameworks
---

# PRD Readiness Review frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/prd-readiness-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite operational reference pack for prd readiness review use cases.

**Industries**: product_management, product_management.prd
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
| `data/prd-readiness-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: PRD completeness checklist, outcome and metric definition, dependency and risk register, decision log governance
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/prd-readiness-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{prd-readiness-review-frameworks_open_harness_hub,
  title  = {PRD Readiness Review frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/prd-readiness-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/prd-readiness-review-frameworks`.
