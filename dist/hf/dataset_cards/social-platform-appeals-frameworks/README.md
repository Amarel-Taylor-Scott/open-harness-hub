---
license: CC-BY-4.0
tags:
- expansion-v5
- experimental
- media.distribution
- open-harness-hub
- retrieval
- social-platform-appeals
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Social Platform Appeals frameworks
---

# Social Platform Appeals frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/social-platform-appeals-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for social platform appeals workflows.

**Industries**: media.distribution, media.distribution
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
| `data/social-platform-appeals/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Social Platform Appeals control checklist, Social Platform Appeals evidence matrix, Social Platform Appeals escalation playbook, Social Platform Appeals benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/social-platform-appeals-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{social-platform-appeals-frameworks_open_harness_hub,
  title  = {Social Platform Appeals frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/social-platform-appeals-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/social-platform-appeals-frameworks`.
