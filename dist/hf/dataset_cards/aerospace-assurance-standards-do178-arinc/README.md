---
license: CC-BY-4.0
tags:
- aviation
- capability-lift
- compliance
- esoteric
- experimental
- government
- ingestion-target
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
pretty_name: Aerospace Assurance Standards Do178 Arinc
---

# Aerospace Assurance Standards Do178 Arinc

<!-- Generated from OpenHubForAI manifest `knowledge-pack/aerospace-assurance-standards-do178-arinc` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: confuse DO-178C DALs vs DO-254 levels; fabricate ARINC 429/653 + ECSS specifics Grounded in RTCA/EUROCAE DO-178C/DO-254 summaries + FAA AC 20-115 + ARINC + ECSS via rag_vector retrieval. Lift: safety-cert DAL->objective mappings exact, niche, version-specific

**Industries**: aviation, compliance, government
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
| `data/esoteric-packs/aerospace-assurance-standards-do178-arinc.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: RTCA/EUROCAE DO-178C/DO-254 summaries + FAA AC 20-115 + ARINC + ECSS
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/aerospace-assurance-standards-do178-arinc.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{aerospace-assurance-standards-do178-arinc_open_harness_hub,
  title  = {Aerospace Assurance Standards Do178 Arinc},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/aerospace-assurance-standards-do178-arinc},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/aerospace-assurance-standards-do178-arinc`.
