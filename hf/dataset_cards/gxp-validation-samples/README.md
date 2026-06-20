---
license: MIT
tags:
- 21-cfr-11
- compliance
- evaluation
- experimental
- gxp
- healthcare.pharmacy
- open-harness-hub
- pharma
- pharma.gxp
- synthetic
- validation
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Synthetic GxP validation samples (3 cases)
---

# Synthetic GxP validation samples (3 cases)

<!-- Generated from Open Harness Hub manifest `dataset/gxp-validation-samples` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Three synthetic GxP-validated-system packets for testing
`pipeline/gxp-validation-review`. Fully synthetic.

Cases:
 - sample-validated-LIMS.json — fully compliant LIMS: audit trail
   on + reviewed quarterly, individual accounts, IQ/OQ/PQ current,
   2-factor signatures, ALCOA+ reviewed. Expected high grade.
 - sample-flagged-MES.json — MES with multiple critical findings:
   audit trail disabled on batch records, shared 'operator-night'
   account, OQ incomplete on a production module, single-factor
   signatures, backup-as-archive, post-hoc backdated alteration.
   Expected many critical findings.
 - sample-mixed-CTMS.json — CTMS mixed: audit trail enabled but
   not reviewed quarterly per risk-based schedule, uncontrolled
   blank CRF templates, batch-approved changes. Mixed signals.

**Industries**: pharma, pharma.gxp, healthcare.pharmacy, compliance
**Capabilities**: evaluation
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Fully synthetic — no real validated-system data
- **collected_by**: Open Harness Hub contributors
- **collected_through**: 2026-05-20
- **license**: MIT
- **anonymization**: fully synthetic; no real pharma facility data

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/gxp-validation-samples.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{gxp-validation-samples_open_harness_hub,
  title  = {Synthetic GxP validation samples (3 cases)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/dataset/gxp-validation-samples},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `dataset/gxp-validation-samples`.
