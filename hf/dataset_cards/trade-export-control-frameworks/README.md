---
license: CC-BY-4.0
tags:
- beta
- bis
- compliance
- ear
- itar
- ofac
- open-harness-hub
- retrieval
- trade
- trade.eccn
- trade.hts
- trade.itar
- trade.sanctions
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Trade & export control frameworks (HTS / EAR / ITAR / OFAC)
---

# Trade & export control frameworks (HTS / EAR / ITAR / OFAC)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/trade-export-control-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite educational reference: HTSUS chapters/headings, EAR
Commerce Control List (Cat 0-9), ITAR USML (Categories I-XXI),
OFAC sanctions programs, BIS Entity List + Unverified List +
MEU list + Section 1260H, BIS red-flag indicators.

**Industries**: trade, trade.hts, trade.eccn, trade.itar, trade.sanctions, compliance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: volatile
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/trade-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: EAR (15 CFR 730-774) (composite extracts), ITAR (22 CFR 120-130) (composite extracts), HTSUS chapter index (composite), OFAC sanctions programs (composite), BIS Red Flag Indicators (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/trade-export-control-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{trade-export-control-frameworks_open_harness_hub,
  title  = {Trade & export control frameworks (HTS / EAR / ITAR / OFAC)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/trade-export-control-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/trade-export-control-frameworks`.
