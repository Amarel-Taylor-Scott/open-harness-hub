---
license: CC-BY-4.0
tags:
- beta
- finance
- open-harness-hub
- retrieval
- tax
- tax.transfer_pricing
- transfer-pricing
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: OECD TP Guidelines + BEPS + Pillar Two + §482
---

# OECD TP Guidelines + BEPS + Pillar Two + §482

<!-- Generated from Open Harness Hub manifest `knowledge-pack/oecd-tp-and-beps` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite of OECD TP Guidelines + BEPS actions + GloBE rules + US §482.

**Industries**: tax, tax.transfer_pricing, finance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/tax-pack/oecd-tp.jsonl` | jsonl | — |

## Provenance

- **sources**: OECD TP Guidelines 2022 (composite), BEPS Actions 5/8-10/13/14 (composite), Pillar Two GloBE rules (composite), US §482 + Treas Reg (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/oecd-tp-and-beps.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{oecd-tp-and-beps_open_harness_hub,
  title  = {OECD TP Guidelines + BEPS + Pillar Two + §482},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/oecd-tp-and-beps},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/oecd-tp-and-beps`.
