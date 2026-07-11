---
license: MIT
tags:
- compliance
- eeoc
- evaluation
- experimental
- hr
- hr.hiring
- open-harness-hub
- synthetic
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Synthetic HR job-posting samples
---

# Synthetic HR job-posting samples

<!-- Generated from OpenHubForAI manifest `dataset/hr-posting-samples` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Two synthetic job postings:
 - clean: senior backend engineer, EEO statement, ADA contact,
   fluency or equivalent. Expected 0 hits.
 - flagged: 'rockstar' / 'ninja' / 'young dynamic team' / 'gentleman's
   club' / native English speaker / US citizen only / salaryman /
   previous salary / family medical history / blanket criminal /
   degree-required-no-equivalent. Expected many hits.

**Industries**: hr, hr.hiring, compliance
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

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/hr-posting-samples.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{hr-posting-samples_open_harness_hub,
  title  = {Synthetic HR job-posting samples},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/dataset/hr-posting-samples},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `dataset/hr-posting-samples`.
