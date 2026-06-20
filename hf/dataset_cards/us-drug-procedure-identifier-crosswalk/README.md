---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- exact_id
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
pretty_name: Us Drug Procedure Identifier Crosswalk
---

# Us Drug Procedure Identifier Crosswalk

<!-- Generated from Open Harness Hub manifest `knowledge-pack/us-drug-procedure-identifier-crosswalk` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: hallucinated NDC/RxCUI/HCPCS codes and NDC->RxNorm->HCPCS crosswalks Grounded in openFDA NDC + NLM RxNorm + CMS HCPCS (free) via exact_id retrieval. Lift: deterministic identifiers churning quarterly; one wrong digit = claim denial

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
| `data/esoteric-packs/us-drug-procedure-identifier-crosswalk.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: openFDA NDC + NLM RxNorm + CMS HCPCS (free)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/us-drug-procedure-identifier-crosswalk.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{us-drug-procedure-identifier-crosswalk_open_harness_hub,
  title  = {Us Drug Procedure Identifier Crosswalk},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/us-drug-procedure-identifier-crosswalk},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/us-drug-procedure-identifier-crosswalk`.
