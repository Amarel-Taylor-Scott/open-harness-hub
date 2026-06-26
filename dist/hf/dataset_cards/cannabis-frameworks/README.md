---
license: CC-BY-4.0
tags:
- beta
- cannabis
- cannabis.cultivation
- cannabis.retail
- cannabis.testing
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
pretty_name: Cannabis regulatory frameworks (state + IRS §280E + METRC + FinCEN)
---

# Cannabis regulatory frameworks (state + IRS §280E + METRC + FinCEN)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/cannabis-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

State licensing + §280E + METRC + FinCEN 2014 + 21 USC 812 + COA panels + ASTM D3475.

**Industries**: cannabis, cannabis.cultivation, cannabis.retail, cannabis.testing
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/cannabis-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: State cannabis licensing (CA BCC / CO MED / NY OCM) composite, IRC §280E composite, METRC + BioTrack seed-to-sale composite, 21 USC 812 Schedule I composite, FinCEN FIN-2014-G001
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/cannabis-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{cannabis-frameworks_open_harness_hub,
  title  = {Cannabis regulatory frameworks (state + IRS §280E + METRC + FinCEN)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/cannabis-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/cannabis-frameworks`.
