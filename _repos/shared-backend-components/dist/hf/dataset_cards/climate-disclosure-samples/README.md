---
license: MIT
tags:
- climate
- esg
- evaluation
- experimental
- finance
- open-harness-hub
- synthetic
- tcfd
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Synthetic climate disclosure samples (2 cases)
---

# Synthetic climate disclosure samples (2 cases)

<!-- Generated from OpenHubForAI manifest `dataset/climate-disclosure-samples` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Two synthetic corporate climate disclosures for testing
`pipeline/climate-disclosure-review`:
 - sample-disclosure-good.json — Acme Corp, manufacturing, board
   oversight quarterly + 1.5C-aligned transition plan + SBTi
   validated + Scope 3 all 15 categories + ISAE 3410 assurance.
   Expected ~1 finding (offsetting language without disclosure).
 - sample-disclosure-flagged.json — Generic Industries, extractive,
   no board oversight + no transition plan + no Scope 3 + no SBTi
   + no scenario analysis + offset-only pathway. Expected ~9
   findings (2 critical / 5 high / 2 medium).

**Industries**: climate, esg, finance
**Capabilities**: evaluation
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Fully synthetic — no real corporate data
- **collected_by**: OpenHubForAI contributors
- **collected_through**: 2026-05-20
- **license**: MIT
- **anonymization**: fully synthetic; no real company info

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/climate-disclosure-samples.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{climate-disclosure-samples_open_harness_hub,
  title  = {Synthetic climate disclosure samples (2 cases)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/dataset/climate-disclosure-samples},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `dataset/climate-disclosure-samples`.
