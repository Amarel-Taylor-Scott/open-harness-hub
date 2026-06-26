---
license: CC-BY-4.0
tags:
- airport-slot-coordination
- aviation.flight_crew
- expansion-v6
- experimental
- government.regulatory
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
pretty_name: Airport Slot Coordination frameworks
---

# Airport Slot Coordination frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/airport-slot-coordination-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for airport slot coordination workflows.

**Industries**: aviation.flight_crew, government.regulatory
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
| `data/airport-slot-coordination/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Airport Slot Coordination control checklist, Airport Slot Coordination evidence matrix, Airport Slot Coordination escalation playbook, Airport Slot Coordination benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/airport-slot-coordination-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{airport-slot-coordination-frameworks_open_harness_hub,
  title  = {Airport Slot Coordination frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/airport-slot-coordination-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/airport-slot-coordination-frameworks`.
