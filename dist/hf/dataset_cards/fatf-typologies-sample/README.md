---
license: CC-BY-4.0
tags:
- experimental
- finance
- finance.aml
- open-harness-hub
- retrieval
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: FATF typologies (sample chunks)
---

# FATF typologies (sample chunks)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/fatf-typologies-sample` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Sample paraphrased typology chunks for catalog-demo purposes. Real
deployments should ingest the latest FATF and FinCEN typology
reports; this pack anchors the data shape and citation pattern.

**Industries**: finance, finance.aml
**Capabilities**: retrieval
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/fatf-typologies.jsonl` | jsonl | — |

## Provenance

- **sources**: Composite paraphrases of public FATF typology reports
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/fatf-typologies-sample.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{fatf-typologies-sample_open_harness_hub,
  title  = {FATF typologies (sample chunks)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/fatf-typologies-sample},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub artifact: `knowledge-pack/fatf-typologies-sample`.
