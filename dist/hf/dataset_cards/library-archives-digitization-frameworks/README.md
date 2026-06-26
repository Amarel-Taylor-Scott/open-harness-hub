---
license: CC-BY-4.0
tags:
- education.higher
- expansion-v6
- experimental
- library-archives-digitization
- media.editorial
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
pretty_name: Library Archives Digitization frameworks
---

# Library Archives Digitization frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/library-archives-digitization-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for library archives digitization workflows.

**Industries**: education.higher, media.editorial
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
| `data/library-archives-digitization/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Library Archives Digitization control checklist, Library Archives Digitization evidence matrix, Library Archives Digitization escalation playbook, Library Archives Digitization benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/library-archives-digitization-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{library-archives-digitization-frameworks_open_harness_hub,
  title  = {Library Archives Digitization frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/library-archives-digitization-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/library-archives-digitization-frameworks`.
