---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- government
- ingestion-target
- knowledge-pack
- maritime
- open-harness-hub
- rag_vector
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
pretty_name: Fmcsa Hours Of Service Eld Exceptions
---

# Fmcsa Hours Of Service Eld Exceptions

<!-- Generated from Open Harness Hub manifest `knowledge-pack/fmcsa-hours-of-service-eld-exceptions` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: garble 11/14/60/70 limits, 30-min break, split-sleeper pairings, exceptions Grounded in FMCSA 49 CFR 395 + HOS/ELD guidance (public domain) via rag_vector retrieval. Lift: exact interacting numeric limits + enumerated exceptions; split-sleeper logic

**Industries**: transportation, maritime, compliance, government
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
| `data/esoteric-packs/fmcsa-hours-of-service-eld-exceptions.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: FMCSA 49 CFR 395 + HOS/ELD guidance (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/fmcsa-hours-of-service-eld-exceptions.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{fmcsa-hours-of-service-eld-exceptions_open_harness_hub,
  title  = {Fmcsa Hours Of Service Eld Exceptions},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/fmcsa-hours-of-service-eld-exceptions},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/fmcsa-hours-of-service-eld-exceptions`.
