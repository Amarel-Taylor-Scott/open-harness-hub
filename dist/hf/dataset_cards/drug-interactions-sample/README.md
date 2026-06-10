---
license: CC-BY-4.0
tags:
- ddi
- drug-interactions
- experimental
- healthcare
- healthcare.clinical
- healthcare.pharmacy
- open-harness-hub
- pharmacy
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Drug-drug interactions (sample, educational)
---

# Drug-drug interactions (sample, educational)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/drug-interactions-sample` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite paraphrases of well-known drug-drug interaction patterns
for educational reference. NOT a substitute for an authoritative
database (e.g. RxNorm + Lexicomp + Micromedex). Each entry carries
drugA / drugB / severity / mechanism / management.

**Industries**: healthcare, healthcare.pharmacy, healthcare.clinical
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/drug-interactions.jsonl` | jsonl | — |

## Provenance

- **sources**: Composite paraphrases of public drug-interaction references.
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/drug-interactions-sample.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{drug-interactions-sample_open_harness_hub,
  title  = {Drug-drug interactions (sample, educational)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/drug-interactions-sample},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub artifact: `knowledge-pack/drug-interactions-sample`.
