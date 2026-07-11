---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- experimental
- graph
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
pretty_name: Quantifier Grounded Set Membership
---

# Quantifier Grounded Set Membership

<!-- Generated from OpenHubForAI manifest `knowledge-pack/quantifier-grounded-set-membership` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: misinterprets all/some/no/most/at-least-k; asserts unsupported universals Grounded in Wikidata enumerated sets (CC0) as membership ground truth via graph retrieval. Lift: Quantifier Comprehension (2306.07384): inverse-scaling; resolve against retrieved set = counted truth

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
| `data/esoteric-packs/quantifier-grounded-set-membership.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Wikidata enumerated sets (CC0) as membership ground truth
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/quantifier-grounded-set-membership.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{quantifier-grounded-set-membership_open_harness_hub,
  title  = {Quantifier Grounded Set Membership},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/quantifier-grounded-set-membership},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/quantifier-grounded-set-membership`.
