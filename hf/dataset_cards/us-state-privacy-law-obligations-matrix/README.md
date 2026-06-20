---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- ingestion-target
- knowledge-pack
- legal
- open-harness-hub
- privacy
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
pretty_name: Us State Privacy Law Obligations Matrix
---

# Us State Privacy Law Obligations Matrix

<!-- Generated from Open Harness Hub manifest `knowledge-pack/us-state-privacy-law-obligations-matrix` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: can't track fast-growing US state privacy patchwork thresholds/opt-out/cure/effective dates Grounded in state privacy statutes (VCDPA/CPA/CTDPA/TDPSA/…) + AG rules (public) via rag_vector retrieval. Lift: dozen-plus recently-effective regimes with differing mechanics; conflated w/ GDPR/CCPA

**Industries**: privacy, compliance, legal
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
| `data/esoteric-packs/us-state-privacy-law-obligations-matrix.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: state privacy statutes (VCDPA/CPA/CTDPA/TDPSA/…) + AG rules (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/us-state-privacy-law-obligations-matrix.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{us-state-privacy-law-obligations-matrix_open_harness_hub,
  title  = {Us State Privacy Law Obligations Matrix},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/us-state-privacy-law-obligations-matrix},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/us-state-privacy-law-obligations-matrix`.
