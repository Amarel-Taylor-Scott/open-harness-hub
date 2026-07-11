---
license: CC-BY-4.0
tags:
- customs-origin-fta
- customs.fta
- expansion-v4
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
pretty_name: Customs Origin FTA frameworks
---

# Customs Origin FTA frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/customs-origin-fta-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for customs origin fta review, evidence, escalation, and benchmarking.

**Industries**: customs.fta, trade.hts
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
| `data/customs-origin-fta/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Customs Origin FTA control checklist, Customs Origin FTA evidence matrix, Customs Origin FTA escalation playbook, Customs Origin FTA benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/customs-origin-fta-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{customs-origin-fta-frameworks_open_harness_hub,
  title  = {Customs Origin FTA frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/customs-origin-fta-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/customs-origin-fta-frameworks`.
