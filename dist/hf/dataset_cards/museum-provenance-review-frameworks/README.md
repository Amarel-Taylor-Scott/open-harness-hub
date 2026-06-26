---
license: CC-BY-4.0
tags:
- expansion-v6
- experimental
- legal.compliance
- museum-provenance-review
- nonprofit
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
pretty_name: Museum Provenance Review frameworks
---

# Museum Provenance Review frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/museum-provenance-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for museum provenance review workflows.

**Industries**: nonprofit, legal.compliance
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
| `data/museum-provenance-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Museum Provenance Review control checklist, Museum Provenance Review evidence matrix, Museum Provenance Review escalation playbook, Museum Provenance Review benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/museum-provenance-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{museum-provenance-review-frameworks_open_harness_hub,
  title  = {Museum Provenance Review frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/museum-provenance-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/museum-provenance-review-frameworks`.
