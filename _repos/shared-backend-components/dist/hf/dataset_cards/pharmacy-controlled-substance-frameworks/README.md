---
license: CC-BY-4.0
tags:
- compliance
- expansion-v6
- experimental
- healthcare.pharmacy
- open-harness-hub
- pharmacy-controlled-substance
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Pharmacy Controlled Substance frameworks
---

# Pharmacy Controlled Substance frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/pharmacy-controlled-substance-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for pharmacy controlled substance workflows.

**Industries**: healthcare.pharmacy, compliance
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
| `data/pharmacy-controlled-substance/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Pharmacy Controlled Substance control checklist, Pharmacy Controlled Substance evidence matrix, Pharmacy Controlled Substance escalation playbook, Pharmacy Controlled Substance benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/pharmacy-controlled-substance-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{pharmacy-controlled-substance-frameworks_open_harness_hub,
  title  = {Pharmacy Controlled Substance frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/pharmacy-controlled-substance-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/pharmacy-controlled-substance-frameworks`.
