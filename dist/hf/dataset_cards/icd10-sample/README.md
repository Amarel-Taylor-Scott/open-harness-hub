---
license: CC0-1.0
tags:
- codes
- experimental
- healthcare
- healthcare.clinical
- icd10
- open-harness-hub
- retrieval
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: ICD-10 sample
---

# ICD-10 sample

<!-- Generated from Open Harness Hub manifest `knowledge-pack/icd10-sample` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Sampled subset of ICD-10 diagnosis codes for catalog-demo purposes.
Use the public, full ICD-10 release for any production deployment;
this pack exists to anchor the data shape, not to be authoritative.

**Industries**: healthcare, healthcare.clinical
**Capabilities**: retrieval
**Modalities**: text, structured
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/icd10-sample.jsonl` | jsonl | — |

## Provenance

- **sources**: WHO ICD-10 public release
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/icd10-sample.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{icd10-sample_open_harness_hub,
  title  = {ICD-10 sample},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/icd10-sample},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC0-1.0`. Hub artifact: `knowledge-pack/icd10-sample`.
