---
license: CC-BY-4.0
tags:
- abi
- beta
- caif
- finance
- fraud
- insurance
- insurance.claims
- insurance.fraud
- naic
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
pretty_name: Insurance fraud typologies (NAIC + CAIF + ABI)
---

# Insurance fraud typologies (NAIC + CAIF + ABI)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/insurance-fraud-typologies` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference of insurance-fraud typologies and red-flag
indicators across personal auto, property, workers-comp, and
health insurance. Sourced from NAIC Fraud Section + Coalition
Against Insurance Fraud (CAIF) + UK Association of British
Insurers (ABI) Insurance Fraud Bureau bulletins.

**Industries**: insurance, insurance.claims, insurance.fraud, finance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: volatile
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/insurance-pack/typologies.jsonl` | jsonl | — |

## Provenance

- **sources**: NAIC Insurance Fraud handbook (composite extracts), Coalition Against Insurance Fraud bulletins (composite), UK ABI Insurance Fraud Bureau typologies (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/insurance-fraud-typologies.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{insurance-fraud-typologies_open_harness_hub,
  title  = {Insurance fraud typologies (NAIC + CAIF + ABI)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/insurance-fraud-typologies},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/insurance-fraud-typologies`.
