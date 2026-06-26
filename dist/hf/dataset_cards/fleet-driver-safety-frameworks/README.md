---
license: CC-BY-4.0
tags:
- automotive.fleet
- expansion-v5
- experimental
- fleet-driver-safety
- open-harness-hub
- retrieval
- transportation.trucking
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Fleet Driver Safety frameworks
---

# Fleet Driver Safety frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/fleet-driver-safety-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for fleet driver safety workflows.

**Industries**: automotive.fleet, transportation.trucking
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
| `data/fleet-driver-safety/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Fleet Driver Safety control checklist, Fleet Driver Safety evidence matrix, Fleet Driver Safety escalation playbook, Fleet Driver Safety benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/fleet-driver-safety-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{fleet-driver-safety-frameworks_open_harness_hub,
  title  = {Fleet Driver Safety frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/fleet-driver-safety-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/fleet-driver-safety-frameworks`.
