---
license: CC-BY-4.0
tags:
- agriculture
- capability-lift
- esoteric
- experimental
- food
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
pretty_name: Fsis Meat Poultry Haccp Rules
---

# Fsis Meat Poultry Haccp Rules

<!-- Generated from OpenHubForAI manifest `knowledge-pack/fsis-meat-poultry-haccp-rules` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: confuse FSIS vs FDA authority; miss Salmonella/lethality/cooling performance standards Grounded in USDA FSIS 9 CFR + HACCP/cooking-cooling directives (public domain) via rag_vector retrieval. Lift: distinct regulator with own numeric standards; models default to generic FDA

**Industries**: agriculture, food
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
| `data/esoteric-packs/fsis-meat-poultry-haccp-rules.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: USDA FSIS 9 CFR + HACCP/cooking-cooling directives (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/fsis-meat-poultry-haccp-rules.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{fsis-meat-poultry-haccp-rules_open_harness_hub,
  title  = {Fsis Meat Poultry Haccp Rules},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/fsis-meat-poultry-haccp-rules},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/fsis-meat-poultry-haccp-rules`.
