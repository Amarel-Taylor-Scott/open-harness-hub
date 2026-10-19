---
license: CC-BY-4.0
tags:
- capability-lift
- classifier
- cross_industry
- esoteric
- experimental
- ingestion-target
- knowledge-pack
- open-harness-hub
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Machine Text Detection Stylometric Features
---

# Machine Text Detection Stylometric Features

<!-- Generated from Open Harness Hub manifest `knowledge-pack/machine-text-detection-stylometric-features` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: LLM self-report unreliable/gameable; signal is in stylometric/perplexity/token-distribution features Grounded in DAIGT corpus + DAIGT-V2/V4 (CC) via classifier retrieval. Lift: leaderboard won by TF-IDF/char-ngram+GBDT+perplexity, not LLM self-report; feature extractor lifts ROC-AUC

**Industries**: cross_industry
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
| `data/esoteric-packs/machine-text-detection-stylometric-features.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: DAIGT corpus + DAIGT-V2/V4 (CC)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/machine-text-detection-stylometric-features.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{machine-text-detection-stylometric-features_open_harness_hub,
  title  = {Machine Text Detection Stylometric Features},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/machine-text-detection-stylometric-features},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/machine-text-detection-stylometric-features`.
