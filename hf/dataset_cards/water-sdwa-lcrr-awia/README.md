---
license: CC-BY-4.0
tags:
- beta
- open-harness-hub
- retrieval
- verification
- water-utility
- water_utility
- water_utility.lcr
- water_utility.sdwa
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Water utility regulatory pack (SDWA / NPDWR / LCRR / DBPR / AWIA)
---

# Water utility regulatory pack (SDWA / NPDWR / LCRR / DBPR / AWIA)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/water-sdwa-lcrr-awia` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite of EPA drinking water regulations + critical-infrastructure cyber.

**Industries**: water_utility, water_utility.lcr, water_utility.sdwa
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/water-pack/sdwa-frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: EPA 40 CFR 141 NPDWR (composite), Lead and Copper Rule Revisions LCRR (composite), Disinfection Byproducts Rule DBPR (composite), AWIA 2018 §1433 (composite), EPA Public Notification Rule (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts; check ECFR for live regulatory text.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/water-sdwa-lcrr-awia.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{water-sdwa-lcrr-awia_open_harness_hub,
  title  = {Water utility regulatory pack (SDWA / NPDWR / LCRR / DBPR / AWIA)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/water-sdwa-lcrr-awia},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/water-sdwa-lcrr-awia`.
