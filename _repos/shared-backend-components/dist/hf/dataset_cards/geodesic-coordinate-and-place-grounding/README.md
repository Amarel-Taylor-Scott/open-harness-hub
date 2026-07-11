---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- experimental
- graph
- ingestion-target
- knowledge-pack
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
pretty_name: Geodesic Coordinate And Place Grounding
---

# Geodesic Coordinate And Place Grounding

<!-- Generated from OpenHubForAI manifest `knowledge-pack/geodesic-coordinate-and-place-grounding` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: miscomputes great-circle distance/bearing, datum transforms; wrong coordinate-to-place mapping Grounded in GeoNames gazetteer (CC BY 4.0) + WGS84/geodesic formulae via graph retrieval. Lift: GPSBench: weak coordinate ops; gazetteer + geodesic compute supplies what spherical reasoning misses

**Industries**: cross_industry
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
| `data/esoteric-packs/geodesic-coordinate-and-place-grounding.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: GeoNames gazetteer (CC BY 4.0) + WGS84/geodesic formulae
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/geodesic-coordinate-and-place-grounding.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{geodesic-coordinate-and-place-grounding_open_harness_hub,
  title  = {Geodesic Coordinate And Place Grounding},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/geodesic-coordinate-and-place-grounding},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/geodesic-coordinate-and-place-grounding`.
