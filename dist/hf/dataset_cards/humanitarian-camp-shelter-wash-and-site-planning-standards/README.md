---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- exact_id
- experimental
- government
- ingestion-target
- knowledge-pack
- maritime
- open-harness-hub
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
pretty_name: Humanitarian Camp Shelter Wash And Site Planning Standards
---

# Humanitarian Camp Shelter Wash And Site Planning Standards

<!-- Generated from OpenHubForAI manifest `knowledge-pack/humanitarian-camp-shelter-wash-and-site-planning-standards` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: invents camp layouts/figures; misses Sphere water L/person/day, latrine ratios, shelter m2, firebreaks Grounded in Sphere Handbook + UNHCR/IOM Camp Management + IASC WASH (reusable) via exact_id retrieval. Lift: non-commercial; Sphere indicators exact; epidemic/exposure death stakes

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
| `data/esoteric-packs/humanitarian-camp-shelter-wash-and-site-planning-standards.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Sphere Handbook + UNHCR/IOM Camp Management + IASC WASH (reusable)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/humanitarian-camp-shelter-wash-and-site-planning-standards.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{humanitarian-camp-shelter-wash-and-site-planning-standards_open_harness_hub,
  title  = {Humanitarian Camp Shelter Wash And Site Planning Standards},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/humanitarian-camp-shelter-wash-and-site-planning-standards},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/humanitarian-camp-shelter-wash-and-site-planning-standards`.
