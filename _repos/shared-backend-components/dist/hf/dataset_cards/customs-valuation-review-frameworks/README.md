---
license: CC-BY-4.0
tags:
- customs-valuation-review
- customs.entry
- expansion-v6
- experimental
- open-harness-hub
- retrieval
- trade.hts
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Customs Valuation Review frameworks
---

# Customs Valuation Review frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/customs-valuation-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for customs valuation review workflows.

**Industries**: customs.entry, trade.hts
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
| `data/customs-valuation-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Customs Valuation Review control checklist, Customs Valuation Review evidence matrix, Customs Valuation Review escalation playbook, Customs Valuation Review benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/customs-valuation-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{customs-valuation-review-frameworks_open_harness_hub,
  title  = {Customs Valuation Review frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/customs-valuation-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/customs-valuation-review-frameworks`.
