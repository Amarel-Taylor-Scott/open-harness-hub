---
license: CC-BY-4.0
tags:
- beta
- customs
- customs.entry
- customs.fta
- customs.tariff
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
pretty_name: Customs frameworks (US CBP 19 CFR + WCO + UFLPA + USMCA)
---

# Customs frameworks (US CBP 19 CFR + WCO + UFLPA + USMCA)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/customs-cbp-wco-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

19 CFR Parts 142/149/152/174 + 19 USC §1484/1592/1307 + UFLPA + USMCA + WCO SAFE.

**Industries**: customs, customs.entry, customs.tariff, customs.fta
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/customs-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: 19 CFR Parts 142/149/152/174 (composite), 19 USC §1484/1592/1307 (composite), UFLPA P.L. 117-78 (composite), USMCA Ch.4-5 (composite), WCO SAFE Framework (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/customs-cbp-wco-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{customs-cbp-wco-frameworks_open_harness_hub,
  title  = {Customs frameworks (US CBP 19 CFR + WCO + UFLPA + USMCA)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/customs-cbp-wco-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/customs-cbp-wco-frameworks`.
