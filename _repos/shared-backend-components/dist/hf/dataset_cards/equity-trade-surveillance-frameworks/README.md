---
license: CC-BY-4.0
tags:
- compliance
- equity-trade-surveillance
- expansion-v7
- experimental
- finance.trading
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
pretty_name: Equity Trade Surveillance frameworks
---

# Equity Trade Surveillance frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/equity-trade-surveillance-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for equity trade surveillance workflows.

**Industries**: finance.trading, compliance
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
| `data/equity-trade-surveillance/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Equity Trade Surveillance control checklist, Equity Trade Surveillance evidence matrix, Equity Trade Surveillance escalation playbook, Equity Trade Surveillance benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/equity-trade-surveillance-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{equity-trade-surveillance-frameworks_open_harness_hub,
  title  = {Equity Trade Surveillance frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/equity-trade-surveillance-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/equity-trade-surveillance-frameworks`.
