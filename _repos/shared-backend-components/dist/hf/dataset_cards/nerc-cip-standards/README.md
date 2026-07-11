---
license: CC-BY-4.0
tags:
- beta
- cip
- energy
- energy.grid
- nerc
- open-harness-hub
- retrieval
- security
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: NERC CIP standards (CIP-002 to CIP-014)
---

# NERC CIP standards (CIP-002 to CIP-014)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/nerc-cip-standards` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite of NERC CIP standards for Bulk Electric System cyber compliance.

**Industries**: energy, energy.grid, security
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/energy-pack/nerc-cip.jsonl` | jsonl | — |

## Provenance

- **sources**: NERC CIP-002 through CIP-014 (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/nerc-cip-standards.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{nerc-cip-standards_open_harness_hub,
  title  = {NERC CIP standards (CIP-002 to CIP-014)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/nerc-cip-standards},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/nerc-cip-standards`.
