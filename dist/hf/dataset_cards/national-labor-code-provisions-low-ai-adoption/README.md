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
pretty_name: National Labor Code Provisions Low Ai Adoption
---

# National Labor Code Provisions Low Ai Adoption

<!-- Generated from OpenHubForAI manifest `knowledge-pack/national-labor-code-provisions-low-ai-adoption` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: models default to US/EU labor norms and miss national wage/hours/termination/severance provisions of countries with little online legal text Grounded in national labor codes + ILO NATLEX legislative database (ILO, public) via rag_vector retrieval. Lift: thin training data (under-digitized jurisdictions) + low economic incentive = valley; provisions are exact statutory text

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
| `data/esoteric-packs/national-labor-code-provisions-low-ai-adoption.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: national labor codes + ILO NATLEX legislative database (ILO, public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/national-labor-code-provisions-low-ai-adoption.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{national-labor-code-provisions-low-ai-adoption_open_harness_hub,
  title  = {National Labor Code Provisions Low Ai Adoption},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/national-labor-code-provisions-low-ai-adoption},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/national-labor-code-provisions-low-ai-adoption`.
