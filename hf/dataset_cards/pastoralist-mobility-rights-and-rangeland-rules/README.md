---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- experimental
- graph
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
pretty_name: Pastoralist Mobility Rights And Rangeland Rules
---

# Pastoralist Mobility Rights And Rangeland Rules

<!-- Generated from Open Harness Hub manifest `knowledge-pack/pastoralist-mobility-rights-and-rangeland-rules` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: don't know transhumance corridors, grazing reserves, water-point rights, cross-border herd protocols Grounded in AU Pastoralism Framework + IGAD protocols + FAO + national rangeland laws (public) via graph retrieval. Lift: (region x season x corridor x right) graph, under-documented; herder-farmer conflict/famine stakes

**Industries**: trade, supply_chain
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
| `data/esoteric-packs/pastoralist-mobility-rights-and-rangeland-rules.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: AU Pastoralism Framework + IGAD protocols + FAO + national rangeland laws (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/pastoralist-mobility-rights-and-rangeland-rules.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{pastoralist-mobility-rights-and-rangeland-rules_open_harness_hub,
  title  = {Pastoralist Mobility Rights And Rangeland Rules},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/pastoralist-mobility-rights-and-rangeland-rules},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/pastoralist-mobility-rights-and-rangeland-rules`.
