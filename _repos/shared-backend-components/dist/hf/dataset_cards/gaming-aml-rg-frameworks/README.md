---
license: CC-BY-4.0
tags:
- beta
- gaming
- gaming.aml
- gaming.responsible
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
pretty_name: Gaming AML + responsible-gambling frameworks (BSA 31 CFR §1021 + state
  RG)
---

# Gaming AML + responsible-gambling frameworks (BSA 31 CFR §1021 + state RG)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/gaming-aml-rg-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

BSA gaming-industry obligations + state responsible-gambling + UKGC LCCP + match-fixing integrity.

**Industries**: gaming, gaming.aml, gaming.responsible
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/gaming-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: 31 CFR Chapter X §1021 (composite), 31 USC §5311 et seq. BSA (composite), UKGC LCCP (composite), Nevada Gaming Control Act (composite), IBIA Code of Conduct (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/gaming-aml-rg-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{gaming-aml-rg-frameworks_open_harness_hub,
  title  = {Gaming AML + responsible-gambling frameworks (BSA 31 CFR §1021 + state RG)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/gaming-aml-rg-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/gaming-aml-rg-frameworks`.
