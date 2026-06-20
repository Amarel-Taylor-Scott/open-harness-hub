---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- experimental
- ingestion-target
- insurance
- knowledge-pack
- open-harness-hub
- rag_vector
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Catastrophe Fnol Xactimate Adjusting Procedures
---

# Catastrophe Fnol Xactimate Adjusting Procedures

<!-- Generated from Open Harness Hub manifest `knowledge-pack/catastrophe-fnol-xactimate-adjusting-procedures` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: lack ITV/coinsurance-penalty math, ACV/RCV depreciation release, O&P rules, CAT-deductible Grounded in state DOI unfair-claims rules + NFIP/FEMA adjuster manuals + IICRC (public) via rag_vector retrieval. Lift: claims-handling math + ordered documentation steps, formula-exact (not underwriting)

**Industries**: insurance
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
| `data/esoteric-packs/catastrophe-fnol-xactimate-adjusting-procedures.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: state DOI unfair-claims rules + NFIP/FEMA adjuster manuals + IICRC (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/catastrophe-fnol-xactimate-adjusting-procedures.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{catastrophe-fnol-xactimate-adjusting-procedures_open_harness_hub,
  title  = {Catastrophe Fnol Xactimate Adjusting Procedures},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/catastrophe-fnol-xactimate-adjusting-procedures},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/catastrophe-fnol-xactimate-adjusting-procedures`.
