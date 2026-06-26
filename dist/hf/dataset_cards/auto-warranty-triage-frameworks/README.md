---
license: CC-BY-4.0
tags:
- auto-warranty-triage
- automotive
- automotive.warranty
- experimental
- open-harness-hub
- retrieval
- use-case-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Auto Warranty Triage frameworks
---

# Auto Warranty Triage frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/auto-warranty-triage-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite operational reference pack for auto warranty triage use cases.

**Industries**: automotive, automotive.warranty
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`

## Files

| path | format | schema |
|---|---|---|
| `data/auto-warranty-triage/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: warranty policy coverage matrix, repair order evidence review, repeat repair and lemon-law escalation cues, field quality issue coding
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/auto-warranty-triage-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{auto-warranty-triage-frameworks_open_harness_hub,
  title  = {Auto Warranty Triage frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/auto-warranty-triage-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/auto-warranty-triage-frameworks`.
