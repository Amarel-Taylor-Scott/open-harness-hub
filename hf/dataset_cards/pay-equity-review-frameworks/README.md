---
license: CC-BY-4.0
tags:
- compliance
- expansion-v5
- experimental
- hr.compensation
- open-harness-hub
- pay-equity-review
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Pay Equity Review frameworks
---

# Pay Equity Review frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/pay-equity-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for pay equity review workflows.

**Industries**: hr.compensation, compliance
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
| `data/pay-equity-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Pay Equity Review control checklist, Pay Equity Review evidence matrix, Pay Equity Review escalation playbook, Pay Equity Review benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/pay-equity-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{pay-equity-review-frameworks_open_harness_hub,
  title  = {Pay Equity Review frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/pay-equity-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/pay-equity-review-frameworks`.
