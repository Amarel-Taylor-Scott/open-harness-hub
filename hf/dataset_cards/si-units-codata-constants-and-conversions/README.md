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
pretty_name: Si Units Codata Constants And Conversions
---

# Si Units Codata Constants And Conversions

<!-- Generated from Open Harness Hub manifest `knowledge-pack/si-units-codata-constants-and-conversions` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: misremembers constant digits, mishandles unit conversion/dimensional analysis, digit-frequency bias Grounded in NIST/CODATA constants (public domain) + SI Brochure (BIPM) + UCUM via exact_id retrieval. Lift: Fragile Number Sense (2509.06332) + Benford's Curse (2506.01734); grounding removes memorized-magnitude error

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
| `data/esoteric-packs/si-units-codata-constants-and-conversions.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: NIST/CODATA constants (public domain) + SI Brochure (BIPM) + UCUM
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/si-units-codata-constants-and-conversions.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{si-units-codata-constants-and-conversions_open_harness_hub,
  title  = {Si Units Codata Constants And Conversions},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/si-units-codata-constants-and-conversions},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/si-units-codata-constants-and-conversions`.
