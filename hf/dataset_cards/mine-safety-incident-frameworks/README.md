---
license: CC-BY-4.0
tags:
- expansion-v4
- experimental
- mine-safety-incident
- mining.surface
- mining.underground
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
pretty_name: Mine Safety Incident frameworks
---

# Mine Safety Incident frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/mine-safety-incident-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for mine safety incident review, evidence, escalation, and benchmarking.

**Industries**: mining.surface, mining.underground
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
| `data/mine-safety-incident/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Mine Safety Incident control checklist, Mine Safety Incident evidence matrix, Mine Safety Incident escalation playbook, Mine Safety Incident benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/mine-safety-incident-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{mine-safety-incident-frameworks_open_harness_hub,
  title  = {Mine Safety Incident frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/mine-safety-incident-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/mine-safety-incident-frameworks`.
