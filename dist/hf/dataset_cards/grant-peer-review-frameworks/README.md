---
license: CC-BY-4.0
tags:
- education.higher
- expansion-v6
- experimental
- grant-peer-review
- open-harness-hub
- retrieval
- scientific_research.social
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Grant Peer Review frameworks
---

# Grant Peer Review frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/grant-peer-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for grant peer review workflows.

**Industries**: scientific_research.social, education.higher
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
| `data/grant-peer-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Grant Peer Review control checklist, Grant Peer Review evidence matrix, Grant Peer Review escalation playbook, Grant Peer Review benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/grant-peer-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{grant-peer-review-frameworks_open_harness_hub,
  title  = {Grant Peer Review frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/grant-peer-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/grant-peer-review-frameworks`.
