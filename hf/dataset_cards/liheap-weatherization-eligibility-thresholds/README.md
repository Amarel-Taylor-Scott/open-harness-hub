---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- exact_id
- experimental
- government
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
pretty_name: Liheap Weatherization Eligibility Thresholds
---

# Liheap Weatherization Eligibility Thresholds

<!-- Generated from Open Harness Hub manifest `knowledge-pack/liheap-weatherization-eligibility-thresholds` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: lack current LIHEAP/WAP income limits, categorical eligibility, per-unit caps Grounded in HHS LIHEAP Action Transmittals + DOE WAP WPN notices (public domain) via exact_id retrieval. Lift: annually-indexed volatile thresholds; models emit stale numbers confidently

**Industries**: government
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
| `data/esoteric-packs/liheap-weatherization-eligibility-thresholds.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: HHS LIHEAP Action Transmittals + DOE WAP WPN notices (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/liheap-weatherization-eligibility-thresholds.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{liheap-weatherization-eligibility-thresholds_open_harness_hub,
  title  = {Liheap Weatherization Eligibility Thresholds},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/liheap-weatherization-eligibility-thresholds},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/liheap-weatherization-eligibility-thresholds`.
