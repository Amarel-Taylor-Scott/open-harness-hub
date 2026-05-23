---
license: MIT
tags:
- evaluation
- experimental
- fleischner
- healthcare
- healthcare.radiology
- hipaa
- open-harness-hub
- radiology
- rads
- synthetic
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Synthetic radiology report samples (3 cases, fully synthetic)
---

# Synthetic radiology report samples (3 cases, fully synthetic)

<!-- Generated from Open Harness Hub manifest `dataset/radiology-report-samples` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Three synthetic radiology reports for testing
`pipeline/radiology-report-grading`. Fully synthetic — no real
patient data.

Cases:
 - sample-ct-chest-good.json — well-structured CT chest with
   proper Fleischner-compliant disposition (expected high grade)
 - sample-ct-abdomen-flagged.json — CT abdomen/pelvis with
   MULTIPLE quality issues: unredacted PHI (MRN + DOB), thyroid
   nodule without TI-RADS, adrenal mass without workup, lytic
   lesion with definitive "is a metastasis" without differential,
   sub-solid pulm nodule without Fleischner follow-up, prior
   available but no comparison addressed, impression lacks
   recommendation
 - sample-mammo-screening-mixed.json — mammography with proper
   BI-RADS scoring + recommendation, comparison addressed; good
   case overall

**Industries**: healthcare, healthcare.radiology
**Capabilities**: evaluation
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Fully synthetic — no real radiology data
- **collected_by**: Open Harness Hub contributors
- **collected_through**: 2026-05-20
- **license**: MIT
- **anonymization**: fully synthetic; no real patient or facility info

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/radiology-report-samples.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{radiology-report-samples_open_harness_hub,
  title  = {Synthetic radiology report samples (3 cases, fully synthetic)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/dataset/radiology-report-samples},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub artifact: `dataset/radiology-report-samples`.
