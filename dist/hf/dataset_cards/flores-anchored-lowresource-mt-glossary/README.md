---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- experimental
- ingestion-target
- keyword
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
pretty_name: Flores Anchored Lowresource Mt Glossary
---

# Flores Anchored Lowresource Mt Glossary

<!-- Generated from OpenHubForAI manifest `knowledge-pack/flores-anchored-lowresource-mt-glossary` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: quality/term fidelity drop for low-resource languages; invents/back-transliterates terms Grounded in FLORES-200 (CC BY-SA 4.0, NLLB 2207.04672) via keyword retrieval. Lift: NLLB quantifies large gaps; retrieved bilingual term anchor supplies coverage

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
| `data/esoteric-packs/flores-anchored-lowresource-mt-glossary.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: FLORES-200 (CC BY-SA 4.0, NLLB 2207.04672)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/flores-anchored-lowresource-mt-glossary.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{flores-anchored-lowresource-mt-glossary_open_harness_hub,
  title  = {Flores Anchored Lowresource Mt Glossary},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/flores-anchored-lowresource-mt-glossary},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/flores-anchored-lowresource-mt-glossary`.
