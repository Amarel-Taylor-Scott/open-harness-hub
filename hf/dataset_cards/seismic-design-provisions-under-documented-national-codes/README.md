---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- exact_id
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
pretty_name: Seismic Design Provisions Under Documented National Codes
---

# Seismic Design Provisions Under Documented National Codes

<!-- Generated from Open Harness Hub manifest `knowledge-pack/seismic-design-provisions-under-documented-national-codes` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: models cite ASCE7/EC8 defaults; miss national seismic zones/importance factors/base-shear of barely-online codes Grounded in national seismic codes (NSCP, NBC Nepal, SNI, Std 2800) + GEM (public) via exact_id retrieval. Lift: edition/country-specific life-safety constants outside training mainstream; collapse stakes

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
| `data/esoteric-packs/seismic-design-provisions-under-documented-national-codes.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: national seismic codes (NSCP, NBC Nepal, SNI, Std 2800) + GEM (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/seismic-design-provisions-under-documented-national-codes.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{seismic-design-provisions-under-documented-national-codes_open_harness_hub,
  title  = {Seismic Design Provisions Under Documented National Codes},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/seismic-design-provisions-under-documented-national-codes},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/seismic-design-provisions-under-documented-national-codes`.
