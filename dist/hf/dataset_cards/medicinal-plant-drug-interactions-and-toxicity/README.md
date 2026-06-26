---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- government
- healthcare
- ingestion-target
- knowledge-pack
- open-harness-hub
- pharma
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
pretty_name: Medicinal Plant Drug Interactions And Toxicity
---

# Medicinal Plant Drug Interactions And Toxicity

<!-- Generated from OpenHubForAI manifest `knowledge-pack/medicinal-plant-drug-interactions-and-toxicity` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: lacks herb-drug interactions (ARVs, TB, anticoagulants), toxic doses, species-confusion risks Grounded in WHO medicinal-plant monographs + traditional-medicine safety + pharmacognosy lit (reusable) via rag_vector retrieval. Lift: thin curated data, low commercial pull; treatment-failure/poisoning stakes

**Industries**: healthcare, pharma, compliance, government
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
| `data/esoteric-packs/medicinal-plant-drug-interactions-and-toxicity.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: WHO medicinal-plant monographs + traditional-medicine safety + pharmacognosy lit (reusable)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/medicinal-plant-drug-interactions-and-toxicity.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{medicinal-plant-drug-interactions-and-toxicity_open_harness_hub,
  title  = {Medicinal Plant Drug Interactions And Toxicity},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/medicinal-plant-drug-interactions-and-toxicity},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/medicinal-plant-drug-interactions-and-toxicity`.
