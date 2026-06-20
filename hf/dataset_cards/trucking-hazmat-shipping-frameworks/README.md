---
license: CC-BY-4.0
tags:
- expansion-v6
- experimental
- open-harness-hub
- retrieval
- trade
- transportation.trucking
- trucking-hazmat-shipping
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Trucking Hazmat Shipping frameworks
---

# Trucking Hazmat Shipping frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/trucking-hazmat-shipping-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for trucking hazmat shipping workflows.

**Industries**: transportation.trucking, trade
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
| `data/trucking-hazmat-shipping/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Trucking Hazmat Shipping control checklist, Trucking Hazmat Shipping evidence matrix, Trucking Hazmat Shipping escalation playbook, Trucking Hazmat Shipping benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/trucking-hazmat-shipping-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{trucking-hazmat-shipping-frameworks_open_harness_hub,
  title  = {Trucking Hazmat Shipping frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/trucking-hazmat-shipping-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/trucking-hazmat-shipping-frameworks`.
