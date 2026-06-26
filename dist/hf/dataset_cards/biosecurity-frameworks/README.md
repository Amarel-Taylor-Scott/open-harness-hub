---
license: CC-BY-4.0
tags:
- beta
- biosecurity
- biosecurity.bsl
- biosecurity.durc
- biosecurity.select_agent
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
pretty_name: Biosecurity frameworks (42 CFR 73 + BMBL 6e + WHO LBM4 + DURC/P3CO)
---

# Biosecurity frameworks (42 CFR 73 + BMBL 6e + WHO LBM4 + DURC/P3CO)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/biosecurity-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

HHS/CDC/APHIS select agent + BMBL 6th + WHO Lab Biosafety Manual 4th + DURC + P3CO.

**Industries**: biosecurity, biosecurity.select_agent, biosecurity.bsl, biosecurity.durc
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/biosecurity-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: 42 CFR Part 73 (composite), 7 CFR 331 / 9 CFR 121 (composite), BMBL 6th Edition CDC/NIH (composite), WHO Laboratory Biosafety Manual 4th (composite), HHS DURC + P3CO Framework (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/biosecurity-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{biosecurity-frameworks_open_harness_hub,
  title  = {Biosecurity frameworks (42 CFR 73 + BMBL 6e + WHO LBM4 + DURC/P3CO)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/biosecurity-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/biosecurity-frameworks`.
