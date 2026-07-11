---
license: MIT
tags:
- claims
- evaluation
- experimental
- finance
- insurance
- insurance.claims
- insurance.fraud
- open-harness-hub
- synthetic
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Synthetic insurance claim samples
---

# Synthetic insurance claim samples

<!-- Generated from OpenHubForAI manifest `dataset/insurance-claim-samples` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Two synthetic insurance claims:
 - sample-claim-clean.json — straightforward rear-end auto claim
   with police report, witness, repair estimate. Expected ~0 hits.
 - sample-claim-flagged.json — property fire with coverage
   increase 12 days before loss, no police report, conflicting
   witnesses, photos pre-date loss, 3 prior claims, IFB warrant
   outstanding. Expected many critical hits.

**Industries**: insurance, insurance.claims, insurance.fraud, finance
**Capabilities**: evaluation
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Fully synthetic — no real claim data
- **collected_by**: OpenHubForAI contributors
- **collected_through**: 2026-05-20
- **license**: MIT
- **anonymization**: fully synthetic

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/insurance-claim-samples.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{insurance-claim-samples_open_harness_hub,
  title  = {Synthetic insurance claim samples},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/dataset/insurance-claim-samples},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `dataset/insurance-claim-samples`.
