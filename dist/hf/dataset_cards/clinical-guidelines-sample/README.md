---
license: CC-BY-4.0
tags:
- experimental
- healthcare
- healthcare.clinical
- open-harness-hub
- retrieval
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Clinical guidelines (sample chunks)
---

# Clinical guidelines (sample chunks)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/clinical-guidelines-sample` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Sample chunks of clinical-guideline language for catalog-demo
purposes. Each chunk has a stable section reference so a
citation-first persona can cite by section. Use authoritative
full-text guidelines (ACC/AHA, NICE, RCP, WHO) for production.

**Industries**: healthcare, healthcare.clinical
**Capabilities**: retrieval
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `citation_edge`

## Files

| path | format | schema |
|---|---|---|
| `data/clinical-guidelines.jsonl` | jsonl | — |

## Provenance

- **sources**: Composite paraphrases of public clinical guidelines
- **collected_through**: 2026-04-30
- **anonymization**: n/a

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/clinical-guidelines-sample.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{clinical-guidelines-sample_open_harness_hub,
  title  = {Clinical guidelines (sample chunks)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/clinical-guidelines-sample},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub artifact: `knowledge-pack/clinical-guidelines-sample`.
