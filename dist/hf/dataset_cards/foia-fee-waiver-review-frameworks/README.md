---
license: CC-BY-4.0
tags:
- expansion-v7
- experimental
- foia-fee-waiver-review
- government.foia
- legal.compliance
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
pretty_name: FOIA Fee Waiver Review frameworks
---

# FOIA Fee Waiver Review frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/foia-fee-waiver-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for foia fee waiver review workflows.

**Industries**: government.foia, legal.compliance
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
| `data/foia-fee-waiver-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: FOIA Fee Waiver Review control checklist, FOIA Fee Waiver Review evidence matrix, FOIA Fee Waiver Review escalation playbook, FOIA Fee Waiver Review benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/foia-fee-waiver-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{foia-fee-waiver-review-frameworks_open_harness_hub,
  title  = {FOIA Fee Waiver Review frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/foia-fee-waiver-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/foia-fee-waiver-review-frameworks`.
