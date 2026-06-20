---
license: CC-BY-4.0
tags:
- capability-lift
- energy
- esoteric
- experimental
- ingestion-target
- knowledge-pack
- open-harness-hub
- regex
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Energy Load Calendar Weather And Lag Features
---

# Energy Load Calendar Weather And Lag Features

<!-- Generated from Open Harness Hub manifest `knowledge-pack/energy-load-calendar-weather-and-lag-features` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: prosumer load/solar needs calendar/holiday/weather/irradiance + lag/rolling + hierarchical structure Grounded in Enefit prosumer + weather/holiday calendars (CC) + M5 hierarchical sales (CC) via regex retrieval. Lift: winning forecasts GBDT over engineered lag/calendar/weather (+M5 reconciliation); feature component lifts MAE

**Industries**: energy
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
| `data/esoteric-packs/energy-load-calendar-weather-and-lag-features.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Enefit prosumer + weather/holiday calendars (CC) + M5 hierarchical sales (CC)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/energy-load-calendar-weather-and-lag-features.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{energy-load-calendar-weather-and-lag-features_open_harness_hub,
  title  = {Energy Load Calendar Weather And Lag Features},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/energy-load-calendar-weather-and-lag-features},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/energy-load-calendar-weather-and-lag-features`.
