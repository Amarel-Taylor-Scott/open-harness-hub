---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- exact_id
- experimental
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
pretty_name: Wikidata Longtail Entity Attributes
---

# Wikidata Longtail Entity Attributes

<!-- Generated from Open Harness Hub manifest `knowledge-pack/wikidata-longtail-entity-attributes` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: accuracy collapses for low-popularity entities/relations; invents plausible-wrong values Grounded in Wikidata statements + qualifiers (CC0) via exact_id retrieval. Lift: PopQA (2212.10511): parametric recall scales with popularity; rare-entity recall near-zero without retrieval

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
| `data/esoteric-packs/wikidata-longtail-entity-attributes.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Wikidata statements + qualifiers (CC0)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/wikidata-longtail-entity-attributes.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{wikidata-longtail-entity-attributes_open_harness_hub,
  title  = {Wikidata Longtail Entity Attributes},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/wikidata-longtail-entity-attributes},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/wikidata-longtail-entity-attributes`.
