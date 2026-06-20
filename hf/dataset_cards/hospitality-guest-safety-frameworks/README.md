---
license: CC-BY-4.0
tags:
- experimental
- hospitality
- hospitality-guest-safety
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
pretty_name: Hospitality Guest Safety frameworks
---

# Hospitality Guest Safety frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/hospitality-guest-safety-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference pack covering incident report completeness, guest injury escalation, hazard correction tracking, security and maintenance evidence preservation.

**Industries**: hospitality
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
| `data/hospitality-guest-safety/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: incident report completeness, guest injury escalation, hazard correction tracking, security and maintenance evidence preservation
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/hospitality-guest-safety-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{hospitality-guest-safety-frameworks_open_harness_hub,
  title  = {Hospitality Guest Safety frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/hospitality-guest-safety-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/hospitality-guest-safety-frameworks`.
