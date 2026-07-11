---
license: CC-BY-4.0
tags:
- capability-lift
- classifier
- esoteric
- experimental
- healthcare
- ingestion-target
- knowledge-pack
- open-harness-hub
- pharma
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Eeg Montage And Harmful Activity Spectrogram Priors
---

# Eeg Montage And Harmful Activity Spectrogram Priors

<!-- Generated from OpenHubForAI manifest `knowledge-pack/eeg-montage-and-harmful-activity-spectrogram-priors` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: harmful-activity patterns live in multichannel time-frequency; no montage/band/spectrogram features Grounded in HMS EEG/spectrogram + expert labels (CC) + 10-20 montage + ACNS defs (public) via classifier retrieval. Lift: won w/ spectrogram CNNs over standardized montages calibrated to rater votes (KL-div); montage+schema enables it

**Industries**: healthcare, pharma
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
| `data/esoteric-packs/eeg-montage-and-harmful-activity-spectrogram-priors.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: HMS EEG/spectrogram + expert labels (CC) + 10-20 montage + ACNS defs (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/eeg-montage-and-harmful-activity-spectrogram-priors.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{eeg-montage-and-harmful-activity-spectrogram-priors_open_harness_hub,
  title  = {Eeg Montage And Harmful Activity Spectrogram Priors},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/eeg-montage-and-harmful-activity-spectrogram-priors},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/eeg-montage-and-harmful-activity-spectrogram-priors`.
