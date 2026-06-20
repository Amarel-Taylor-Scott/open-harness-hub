---
license: CC-BY-4.0
tags:
- agriculture
- capability-lift
- esoteric
- experimental
- food
- ingestion-target
- knowledge-pack
- open-harness-hub
- rag_vector
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Smallholder Agronomy By Agroclimatic Zone
---

# Smallholder Agronomy By Agroclimatic Zone

<!-- Generated from Open Harness Hub manifest `knowledge-pack/smallholder-agronomy-by-agroclimatic-zone` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: models give generic agronomy and miss staple-crop spacing/timing/pest thresholds specific to agroclimatic zones and local varieties Grounded in FAO crop guides + CGIAR/national extension materials (FAO/CGIAR, reusable) via rag_vector retrieval. Lift: zone- and variety-specific, low-digitization, subsistence-economy focus = valley; agronomic facts verifiable

**Industries**: agriculture, food
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
| `data/esoteric-packs/smallholder-agronomy-by-agroclimatic-zone.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: FAO crop guides + CGIAR/national extension materials (FAO/CGIAR, reusable)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/smallholder-agronomy-by-agroclimatic-zone.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{smallholder-agronomy-by-agroclimatic-zone_open_harness_hub,
  title  = {Smallholder Agronomy By Agroclimatic Zone},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/smallholder-agronomy-by-agroclimatic-zone},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/smallholder-agronomy-by-agroclimatic-zone`.
