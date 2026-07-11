---
license: CC-BY-4.0
tags:
- experimental
- media
- media-claims-factcheck
- media.factcheck
- open-harness-hub
- retrieval
- synthetic-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Media Claims Factcheck frameworks
---

# Media Claims Factcheck frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/media-claims-factcheck-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference pack covering claim-evidence matrixing, primary-source preference, quote fidelity review, correction and update workflow.

**Industries**: media, media.factcheck
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `policy_summary`

## Files

| path | format | schema |
|---|---|---|
| `data/media-claims-factcheck/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: claim-evidence matrixing, primary-source preference, quote fidelity review, correction and update workflow
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/media-claims-factcheck-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{media-claims-factcheck-frameworks_open_harness_hub,
  title  = {Media Claims Factcheck frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/media-claims-factcheck-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/media-claims-factcheck-frameworks`.
