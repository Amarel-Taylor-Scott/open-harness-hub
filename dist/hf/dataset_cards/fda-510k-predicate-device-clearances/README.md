---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- exact_id
- experimental
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
pretty_name: Fda 510K Predicate Device Clearances
---

# Fda 510K Predicate Device Clearances

<!-- Generated from OpenHubForAI manifest `knowledge-pack/fda-510k-predicate-device-clearances` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: LLMs invent/misattribute 510(k) K-numbers, predicate chains, product codes, clearance dates Grounded in openFDA 510(k) + Product Classification + GUDID (public domain) via exact_id retrieval. Lift: long-tail factual recall over ~150k weekly-updated clearances keyed by opaque K-numbers

**Industries**: healthcare, pharma
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
| `data/esoteric-packs/fda-510k-predicate-device-clearances.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: openFDA 510(k) + Product Classification + GUDID (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/fda-510k-predicate-device-clearances.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{fda-510k-predicate-device-clearances_open_harness_hub,
  title  = {Fda 510K Predicate Device Clearances},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/fda-510k-predicate-device-clearances},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/fda-510k-predicate-device-clearances`.
