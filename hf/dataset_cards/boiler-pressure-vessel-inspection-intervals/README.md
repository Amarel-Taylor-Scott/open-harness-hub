---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- construction
- esoteric
- experimental
- finance
- graph
- infrastructure
- ingestion-target
- knowledge-pack
- open-harness-hub
- retrieval
- supply_chain
- trade
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Boiler Pressure Vessel Inspection Intervals
---

# Boiler Pressure Vessel Inspection Intervals

<!-- Generated from Open Harness Hub manifest `knowledge-pack/boiler-pressure-vessel-inspection-intervals` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: can't recall NB-23/ASME inspection intervals by state + MAWP recert triggers Grounded in National Board NBIC (NB-23) + state boiler-law adoption tables via graph retrieval. Lift: (vessel-type x state x service) join the model can't do from memory

**Industries**: finance, compliance, trade, supply_chain, construction, infrastructure
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
| `data/esoteric-packs/boiler-pressure-vessel-inspection-intervals.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: National Board NBIC (NB-23) + state boiler-law adoption tables
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/boiler-pressure-vessel-inspection-intervals.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{boiler-pressure-vessel-inspection-intervals_open_harness_hub,
  title  = {Boiler Pressure Vessel Inspection Intervals},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/boiler-pressure-vessel-inspection-intervals},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/boiler-pressure-vessel-inspection-intervals`.
