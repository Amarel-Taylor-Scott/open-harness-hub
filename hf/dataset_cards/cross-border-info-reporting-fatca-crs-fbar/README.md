---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- exact_id
- experimental
- finance
- ingestion-target
- knowledge-pack
- maritime
- open-harness-hub
- retrieval
- transportation
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Cross Border Info Reporting Fatca Crs Fbar
---

# Cross Border Info Reporting Fatca Crs Fbar

<!-- Generated from Open Harness Hub manifest `knowledge-pack/cross-border-info-reporting-fatca-crs-fbar` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: conflate FATCA 8938 vs FBAR 114 thresholds, CRS status, 1042-S chapter-3/4 codes Grounded in IRS FATCA + FinCEN BSA + OECD CRS (public) via exact_id retrieval. Lift: distinct thresholds/forms/codes, high penalties, known conflation failure

**Industries**: finance, compliance, transportation, maritime
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
| `data/esoteric-packs/cross-border-info-reporting-fatca-crs-fbar.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: IRS FATCA + FinCEN BSA + OECD CRS (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/cross-border-info-reporting-fatca-crs-fbar.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{cross-border-info-reporting-fatca-crs-fbar_open_harness_hub,
  title  = {Cross Border Info Reporting Fatca Crs Fbar},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/cross-border-info-reporting-fatca-crs-fbar},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/cross-border-info-reporting-fatca-crs-fbar`.
