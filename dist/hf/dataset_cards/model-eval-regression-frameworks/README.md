---
license: CC-BY-4.0
tags:
- ai
- ai_governance
- expansion-v3
- experimental
- model-eval-regression
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
pretty_name: Model Eval Regression frameworks
---

# Model Eval Regression frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/model-eval-regression-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for model eval regression reviews, including evidence, escalation, and remediation controls.

**Industries**: ai, ai_governance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`
- `evidence_matrix`

## Files

| path | format | schema |
|---|---|---|
| `data/model-eval-regression/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Model Eval Regression control checklist, Model Eval Regression evidence matrix, Model Eval Regression escalation playbook, Model Eval Regression remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/model-eval-regression-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{model-eval-regression-frameworks_open_harness_hub,
  title  = {Model Eval Regression frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/model-eval-regression-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/model-eval-regression-frameworks`.
