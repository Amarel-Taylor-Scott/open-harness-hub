---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- government
- graph
- ingestion-target
- knowledge-pack
- maritime
- open-harness-hub
- retrieval
- transportation
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Port State Control Deficiency Detention Codes
---

# Port State Control Deficiency Detention Codes

<!-- Generated from OpenHubForAI manifest `knowledge-pack/port-state-control-deficiency-detention-codes` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: don't know Paris/Tokyo MoU deficiency codes, detainable criteria, ship-risk profile Grounded in Paris/Tokyo MoU PSC procedures + IMO Res. A.1185 via graph retrieval. Lift: code->convention->action joins defeat memory

**Industries**: transportation, maritime, compliance, government
**Capabilities**: retrieval, verification
**Modalities**: structured, text
**Freshness**: volatile
**Trust boundary**: external

## Content types (leaf vocabulary)

- `fact_table`
- `reference_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/esoteric-packs/port-state-control-deficiency-detention-codes.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Paris/Tokyo MoU PSC procedures + IMO Res. A.1185
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/port-state-control-deficiency-detention-codes.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{port-state-control-deficiency-detention-codes_open_harness_hub,
  title  = {Port State Control Deficiency Detention Codes},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/port-state-control-deficiency-detention-codes},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/port-state-control-deficiency-detention-codes`.
