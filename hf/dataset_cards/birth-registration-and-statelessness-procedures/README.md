---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- experimental
- ingestion-target
- knowledge-pack
- manufacturing
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
pretty_name: Birth Registration And Statelessness Procedures
---

# Birth Registration And Statelessness Procedures

<!-- Generated from Open Harness Hub manifest `knowledge-pack/birth-registration-and-statelessness-procedures` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: LLMs lack country-specific birth-registration, late-registration, and statelessness-determination procedures critical for undocumented populations Grounded in UNHCR statelessness handbook + UNICEF civil-registration guidance + national civil-status codes (public) via rag_vector retrieval. Lift: deeply under-resourced domain, no economic signal, high stakes; procedures are exact and citeable

**Industries**: manufacturing
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
| `data/esoteric-packs/birth-registration-and-statelessness-procedures.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: UNHCR statelessness handbook + UNICEF civil-registration guidance + national civil-status codes (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/birth-registration-and-statelessness-procedures.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{birth-registration-and-statelessness-procedures_open_harness_hub,
  title  = {Birth Registration And Statelessness Procedures},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/birth-registration-and-statelessness-procedures},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/birth-registration-and-statelessness-procedures`.
