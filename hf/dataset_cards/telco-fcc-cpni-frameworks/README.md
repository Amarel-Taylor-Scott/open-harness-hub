---
license: CC-BY-4.0
tags:
- beta
- open-harness-hub
- retrieval
- telco
- telecommunications
- telecommunications.cpni
- telecommunications.fcc
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Telco regulatory frameworks (FCC 47 CFR + CPNI + CALEA + STIR/SHAKEN)
---

# Telco regulatory frameworks (FCC 47 CFR + CPNI + CALEA + STIR/SHAKEN)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/telco-fcc-cpni-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite 47 CFR Part 4 (NORS) / Part 9 (911) / Part 64 (CPNI + STIR/SHAKEN) / CALEA + 47 USC §222.

**Industries**: telecommunications, telecommunications.fcc, telecommunications.cpni
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/telco-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: 47 CFR Parts 4/9/64 (composite), 47 USC §222 CPNI (composite), CALEA 47 USC §1001 (composite), FCC STIR/SHAKEN orders (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/telco-fcc-cpni-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{telco-fcc-cpni-frameworks_open_harness_hub,
  title  = {Telco regulatory frameworks (FCC 47 CFR + CPNI + CALEA + STIR/SHAKEN)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/telco-fcc-cpni-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/telco-fcc-cpni-frameworks`.
