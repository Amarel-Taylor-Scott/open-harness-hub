---
license: CC-BY-4.0
tags:
- ai-policy
- apa
- beta
- compliance
- education
- education.higher
- honor-code
- mla
- open-harness-hub
- plagiarism
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Academic honor codes + AI-policy frameworks
---

# Academic honor codes + AI-policy frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/academic-honor-codes` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite educational reference of academic honor codes, AI-use
policies, plagiarism definitions, and citation standards (APA /
MLA / Chicago).

**Industries**: education, education.higher, compliance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/academic-pack/honor-codes.jsonl` | jsonl | — |

## Provenance

- **sources**: Composite of common honor-code patterns + APA 7 / MLA 9 / Chicago 17 citation rules
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts; each institution has its own canonical honor-code text.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/academic-honor-codes.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{academic-honor-codes_open_harness_hub,
  title  = {Academic honor codes + AI-policy frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/academic-honor-codes},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/academic-honor-codes`.
