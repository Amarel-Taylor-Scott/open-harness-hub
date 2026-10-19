---
license: CC-BY-4.0
tags:
- capability-lift
- classifier
- compliance
- esoteric
- experimental
- finance
- government
- healthcare
- ingestion-target
- knowledge-pack
- open-harness-hub
- pharma
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Bioacoustic Mel Features And Taxonomy Priors
---

# Bioacoustic Mel Features And Taxonomy Priors

<!-- Generated from Open Harness Hub manifest `knowledge-pack/bioacoustic-mel-features-and-taxonomy-priors` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: species ID needs mel-spectrogram + taxonomy + region/season occurrence prior; no audio front end Grounded in BirdCLEF audio+labels (CC) + eBird/Xeno-canto taxonomy/occurrence (CC) via classifier retrieval. Lift: winning combined mel-CNN + taxonomy/region priors (macro ROC-AUC); audio+prior component supplies structure

**Industries**: healthcare, pharma, finance, compliance, government
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
| `data/esoteric-packs/bioacoustic-mel-features-and-taxonomy-priors.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: BirdCLEF audio+labels (CC) + eBird/Xeno-canto taxonomy/occurrence (CC)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/bioacoustic-mel-features-and-taxonomy-priors.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{bioacoustic-mel-features-and-taxonomy-priors_open_harness_hub,
  title  = {Bioacoustic Mel Features And Taxonomy Priors},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/bioacoustic-mel-features-and-taxonomy-priors},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/bioacoustic-mel-features-and-taxonomy-priors`.
