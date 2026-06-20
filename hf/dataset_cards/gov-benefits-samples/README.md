---
license: MIT
tags:
- benefits
- evaluation
- experimental
- government
- government.benefits
- open-harness-hub
- snap
- synthetic
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Synthetic SNAP application samples
---

# Synthetic SNAP application samples

<!-- Generated from Open Harness Hub manifest `dataset/gov-benefits-samples` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Two synthetic SNAP applications:
 - sample-snap-app-clean.json — 3-person household with minor
   children, $1850 gross income (below 130% poverty for HH of 3),
   ID + paystub + residence + school enrollment all verified.
   Expected ~0 hits.
 - sample-snap-app-flagged.json — 1-person household with
   undisclosed adult, $4800 gross income (over threshold),
   unreported self-employment, $6800 in bank (over resource limit),
   ABAWD with only 12 hours/month, active case in another state,
   outstanding fraud warrant. Expected many hits.

**Industries**: government, government.benefits
**Capabilities**: evaluation
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Fully synthetic — no real application data
- **collected_by**: Open Harness Hub contributors
- **collected_through**: 2026-05-20
- **license**: MIT
- **anonymization**: fully synthetic

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/gov-benefits-samples.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{gov-benefits-samples_open_harness_hub,
  title  = {Synthetic SNAP application samples},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/dataset/gov-benefits-samples},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `dataset/gov-benefits-samples`.
