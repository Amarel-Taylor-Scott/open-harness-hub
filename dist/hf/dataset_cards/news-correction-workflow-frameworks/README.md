---
license: CC-BY-4.0
tags:
- expansion-v5
- experimental
- media.editorial
- media.factcheck
- news-correction-workflow
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
pretty_name: News Correction Workflow frameworks
---

# News Correction Workflow frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/news-correction-workflow-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for news correction workflow workflows.

**Industries**: media.editorial, media.factcheck
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
| `data/news-correction-workflow/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: News Correction Workflow control checklist, News Correction Workflow evidence matrix, News Correction Workflow escalation playbook, News Correction Workflow benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/news-correction-workflow-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{news-correction-workflow-frameworks_open_harness_hub,
  title  = {News Correction Workflow frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/news-correction-workflow-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/news-correction-workflow-frameworks`.
