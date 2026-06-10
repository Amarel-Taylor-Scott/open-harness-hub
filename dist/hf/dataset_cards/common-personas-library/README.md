---
license: CC0-1.0
tags:
- beta
- cross_industry
- library
- open-harness-hub
- personas
- retrieval
- system-prompts
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Common personas / system-prompt library
---

# Common personas / system-prompt library

<!-- Generated from Open Harness Hub manifest `knowledge-pack/common-personas-library` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reusable persona / system-prompt fragments for common roles —
research analyst, code reviewer, customer-support agent, technical
writer, translator, tutor, summarizer, fact-checker, plain-language
rewriter. Each row is a self-contained system prompt the
`inject.persona` processor or any harness can drop in.

**Industries**: cross_industry
**Capabilities**: retrieval
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `persona_block`

## Files

| path | format | schema |
|---|---|---|
| `data/common-personas.jsonl` | jsonl | — |

## Provenance

- **sources**: Composed by Open Harness Hub contributors. Public domain.
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/common-personas-library.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{common-personas-library_open_harness_hub,
  title  = {Common personas / system-prompt library},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/common-personas-library},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC0-1.0`. Hub artifact: `knowledge-pack/common-personas-library`.
