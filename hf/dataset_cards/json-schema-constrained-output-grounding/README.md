---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- experimental
- ingestion-target
- knowledge-pack
- open-harness-hub
- regex
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Json Schema Constrained Output Grounding
---

# Json Schema Constrained Output Grounding

<!-- Generated from Open Harness Hub manifest `knowledge-pack/json-schema-constrained-output-grounding` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: schema-invalid JSON (missing required, wrong types/enums); reasoning degrades under format constraints Grounded in JSON Schema Store + JSONSchemaBench (2501.10868) via regex retrieval. Lift: JSONSchemaBench: unconstrained LLMs fail hard schemas; retrieve+validate enforces adherence

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
| `data/esoteric-packs/json-schema-constrained-output-grounding.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: JSON Schema Store + JSONSchemaBench (2501.10868)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/json-schema-constrained-output-grounding.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{json-schema-constrained-output-grounding_open_harness_hub,
  title  = {Json Schema Constrained Output Grounding},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/json-schema-constrained-output-grounding},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/json-schema-constrained-output-grounding`.
