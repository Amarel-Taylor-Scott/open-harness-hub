---
license: CC-BY-4.0
tags:
- cyber.soc
- expansion-v7
- experimental
- open-harness-hub
- retrieval
- security.defensive
- soc-alert-quality
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: SOC Alert Quality frameworks
---

# SOC Alert Quality frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/soc-alert-quality-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for soc alert quality workflows.

**Industries**: cyber.soc, security.defensive
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
| `data/soc-alert-quality/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: SOC Alert Quality control checklist, SOC Alert Quality evidence matrix, SOC Alert Quality escalation playbook, SOC Alert Quality benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/soc-alert-quality-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{soc-alert-quality-frameworks_open_harness_hub,
  title  = {SOC Alert Quality frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/soc-alert-quality-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/soc-alert-quality-frameworks`.
