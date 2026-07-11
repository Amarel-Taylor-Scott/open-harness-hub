---
license: CC-BY-4.0
tags:
- construction.safety
- expansion-v7
- experimental
- infrastructure.tunnel
- open-harness-hub
- retrieval
- tunnel-ventilation-safety
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Tunnel Ventilation Safety frameworks
---

# Tunnel Ventilation Safety frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/tunnel-ventilation-safety-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for tunnel ventilation safety workflows.

**Industries**: infrastructure.tunnel, construction.safety
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
| `data/tunnel-ventilation-safety/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Tunnel Ventilation Safety control checklist, Tunnel Ventilation Safety evidence matrix, Tunnel Ventilation Safety escalation playbook, Tunnel Ventilation Safety benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/tunnel-ventilation-safety-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{tunnel-ventilation-safety-frameworks_open_harness_hub,
  title  = {Tunnel Ventilation Safety frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/tunnel-ventilation-safety-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/tunnel-ventilation-safety-frameworks`.
