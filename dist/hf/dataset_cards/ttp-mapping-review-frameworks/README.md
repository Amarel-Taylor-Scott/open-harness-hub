---
license: CC-BY-4.0
tags:
- expansion-v7
- experimental
- open-harness-hub
- retrieval
- security.defensive
- threat_intelligence.ttp
- ttp-mapping-review
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: TTP Mapping Review frameworks
---

# TTP Mapping Review frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/ttp-mapping-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for ttp mapping review workflows.

**Industries**: threat_intelligence.ttp, security.defensive
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
| `data/ttp-mapping-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: TTP Mapping Review control checklist, TTP Mapping Review evidence matrix, TTP Mapping Review escalation playbook, TTP Mapping Review benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/ttp-mapping-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{ttp-mapping-review-frameworks_open_harness_hub,
  title  = {TTP Mapping Review frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/ttp-mapping-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/ttp-mapping-review-frameworks`.
