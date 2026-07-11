---
license: CC-BY-4.0
tags:
- creative.game
- expansion-v4
- experimental
- game-content-safety
- media.distribution
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
pretty_name: Game Content Safety frameworks
---

# Game Content Safety frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/game-content-safety-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for game content safety review, evidence, escalation, and benchmarking.

**Industries**: creative.game, media.distribution
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
| `data/game-content-safety/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Game Content Safety control checklist, Game Content Safety evidence matrix, Game Content Safety escalation playbook, Game Content Safety benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/game-content-safety-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{game-content-safety-frameworks_open_harness_hub,
  title  = {Game Content Safety frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/game-content-safety-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/game-content-safety-frameworks`.
