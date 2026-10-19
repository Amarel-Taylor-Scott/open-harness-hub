---
license: CC-BY-4.0
tags:
- compliance
- experimental
- finance
- finance-lending-fairness
- finance.lending
- open-harness-hub
- retrieval
- synthetic-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Finance Lending Fairness frameworks
---

# Finance Lending Fairness frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/finance-lending-fairness-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference pack covering ECOA adverse action notices, Regulation B documentation, disparate impact proxy monitoring, model override governance.

**Industries**: finance, finance.lending, compliance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `policy_summary`

## Files

| path | format | schema |
|---|---|---|
| `data/finance-lending-fairness/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: ECOA adverse action notices, Regulation B documentation, disparate impact proxy monitoring, model override governance
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/finance-lending-fairness-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{finance-lending-fairness-frameworks_open_harness_hub,
  title  = {Finance Lending Fairness frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/finance-lending-fairness-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/finance-lending-fairness-frameworks`.
