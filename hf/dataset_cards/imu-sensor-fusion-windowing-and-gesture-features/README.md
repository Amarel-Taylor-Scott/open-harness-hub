---
license: CC-BY-4.0
tags:
- capability-lift
- classifier
- cross_industry
- esoteric
- experimental
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
pretty_name: Imu Sensor Fusion Windowing And Gesture Features
---

# Imu Sensor Fusion Windowing And Gesture Features

<!-- Generated from Open Harness Hub manifest `knowledge-pack/imu-sensor-fusion-windowing-and-gesture-features` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: behavior detection in multi-rate IMU/ToF/thermopile needs gravity removal, resample, orientation-invariant features Grounded in CMI Detect Behavior sensor data + labels (CC) + IMU preprocessing refs (public) via classifier retrieval. Lift: gains from sensor-fusion preprocessing + 1D-CNN on windowed signals; fusion+windowing component supplies it

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
| `data/esoteric-packs/imu-sensor-fusion-windowing-and-gesture-features.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: CMI Detect Behavior sensor data + labels (CC) + IMU preprocessing refs (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/imu-sensor-fusion-windowing-and-gesture-features.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{imu-sensor-fusion-windowing-and-gesture-features_open_harness_hub,
  title  = {Imu Sensor Fusion Windowing And Gesture Features},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/imu-sensor-fusion-windowing-and-gesture-features},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/imu-sensor-fusion-windowing-and-gesture-features`.
