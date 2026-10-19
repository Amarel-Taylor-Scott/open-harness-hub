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
pretty_name: Us State Sales Tax Economic Nexus Thresholds
---

# Us State Sales Tax Economic Nexus Thresholds

<!-- Generated from Open Harness Hub manifest `knowledge-pack/us-state-sales-tax-economic-nexus-thresholds` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: can't recall per-state post-Wayfair nexus thresholds, marketplace-facilitator rules Grounded in state DOR statutes + Streamlined Sales Tax Board (public) via exact_id retrieval. Lift: 50+ jurisdiction-specific frequently-amended numeric thresholds

**Industries**: finance, compliance
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
| `data/esoteric-packs/us-state-sales-tax-economic-nexus-thresholds.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: state DOR statutes + Streamlined Sales Tax Board (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/us-state-sales-tax-economic-nexus-thresholds.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{us-state-sales-tax-economic-nexus-thresholds_open_harness_hub,
  title  = {Us State Sales Tax Economic Nexus Thresholds},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/us-state-sales-tax-economic-nexus-thresholds},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/us-state-sales-tax-economic-nexus-thresholds`.
