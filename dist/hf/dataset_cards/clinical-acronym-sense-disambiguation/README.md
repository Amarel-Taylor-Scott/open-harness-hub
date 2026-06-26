---
license: CC-BY-4.0
tags:
- capability-lift
- classifier
- esoteric
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
pretty_name: Clinical Acronym Sense Disambiguation
---

# Clinical Acronym Sense Disambiguation

<!-- Generated from OpenHubForAI manifest `knowledge-pack/clinical-acronym-sense-disambiguation` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: ambiguous acronyms (RA=rheumatoid arthritis vs right atrium vs room air); picks frequent-wrong sense Grounded in MeSH descriptors/entry terms (NLM, freely reproducible) via classifier retrieval. Lift: JAMIA 2024 + MeDAL: non-trivial error; context-conditioned sense classifier over closed inventory

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
| `data/esoteric-packs/clinical-acronym-sense-disambiguation.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: MeSH descriptors/entry terms (NLM, freely reproducible)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/clinical-acronym-sense-disambiguation.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{clinical-acronym-sense-disambiguation_open_harness_hub,
  title  = {Clinical Acronym Sense Disambiguation},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/clinical-acronym-sense-disambiguation},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/clinical-acronym-sense-disambiguation`.
