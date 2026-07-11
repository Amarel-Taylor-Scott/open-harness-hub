---
license: MIT
tags:
- compliance
- dsar
- evaluation
- experimental
- gdpr
- open-harness-hub
- privacy
- privacy.dsar
- privacy.gdpr
- synthetic
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Synthetic GDPR DSAR samples
---

# Synthetic GDPR DSAR samples

<!-- Generated from OpenHubForAI manifest `dataset/gdpr-dsar-samples` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Two synthetic DSARs:
 - clean: identity verified, 14-day response, all Art. 15 fields,
   no-transfer, free of charge. Expected 0 hits.
 - flagged: 2.5 months past deadline, no identity verification,
   no lawful basis, US transfer without SCC, $25 charge, erasure
   refused without basis, special-category without art 9(2),
   breach notification delayed. Expected many critical hits.

**Industries**: privacy, privacy.gdpr, privacy.dsar, compliance
**Capabilities**: evaluation
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Fully synthetic
- **collected_by**: OpenHubForAI contributors
- **collected_through**: 2026-05-20
- **license**: MIT
- **anonymization**: fully synthetic

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/gdpr-dsar-samples.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{gdpr-dsar-samples_open_harness_hub,
  title  = {Synthetic GDPR DSAR samples},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/dataset/gdpr-dsar-samples},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `dataset/gdpr-dsar-samples`.
