---
license: MIT
tags:
- contract
- evaluation
- experimental
- legal
- legal.compliance
- legal.contract
- msa
- nda
- open-harness-hub
- synthetic
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Synthetic commercial contract samples (3 cases)
---

# Synthetic commercial contract samples (3 cases)

<!-- Generated from Open Harness Hub manifest `dataset/contract-samples` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Three synthetic commercial contracts for testing
`pipeline/contract-clause-review`. Fully synthetic — no real
contract data.

Cases:
 - sample-msa-clean.json — well-drafted MSA with all critical
   clauses present (capped indemnity with carve-outs, mutual
   liability cap, DPA attached, audit rights, anti-bribery
   warranty, 90-day termination with wind-down, symmetric
   assignment, broad force-majeure). Expected high grade.
 - sample-vendor-flagged.json — aggressive vendor agreement
   with 9 red flags (uncapped indemnity to vendor, $10k
   vendor cap vs unlimited customer liability, IP assignment
   of pre-existing IP, no residuals, no DPA, no audit rights,
   no anti-bribery, 5-day termination, free vendor assignment,
   narrow force-majeure). Expected highly flagged.
 - sample-nda-mixed.json — NDA missing residuals clause + 5y
   term (long but not red-flag). Mixed signals.

**Industries**: legal, legal.contract, legal.compliance
**Capabilities**: evaluation
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Fully synthetic — no real contract data
- **collected_by**: Open Harness Hub contributors
- **collected_through**: 2026-05-20
- **license**: MIT
- **anonymization**: fully synthetic; no real entities

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/contract-samples.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{contract-samples_open_harness_hub,
  title  = {Synthetic commercial contract samples (3 cases)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/dataset/contract-samples},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub artifact: `dataset/contract-samples`.
