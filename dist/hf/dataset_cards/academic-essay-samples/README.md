---
license: MIT
tags:
- ai-detection
- compliance
- education
- education.higher
- evaluation
- experimental
- open-harness-hub
- plagiarism
- synthetic
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Synthetic academic essay samples (integrity-review test set)
---

# Synthetic academic essay samples (integrity-review test set)

<!-- Generated from OpenHubForAI manifest `dataset/academic-essay-samples` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Two synthetic student-essay submissions:
 - sample-essay-clean.json — proper Aristotle / Kant / Mill /
   Hursthouse citations, no AI artefacts, AI-disclosure present.
 - sample-essay-flagged.json — opens with "As an AI language
   model", uses "my knowledge cutoff", filler phrases throughout,
   fabricated DOI. Expected many AI-misuse hits.

**Industries**: education, education.higher, compliance
**Capabilities**: evaluation
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Fully synthetic — no real student data
- **collected_by**: OpenHubForAI contributors
- **collected_through**: 2026-05-20
- **license**: MIT
- **anonymization**: fully synthetic

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/academic-essay-samples.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{academic-essay-samples_open_harness_hub,
  title  = {Synthetic academic essay samples (integrity-review test set)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/dataset/academic-essay-samples},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `dataset/academic-essay-samples`.
