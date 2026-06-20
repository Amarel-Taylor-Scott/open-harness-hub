---
license: CC0-1.0
tags:
- beta
- cross_industry
- open-harness-hub
- personal
- preferences
- retrieval
- template
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Personal preferences template (fork + edit)
---

# Personal preferences template (fork + edit)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/personal-preferences-template` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

A template knowledge pack that holds a single user's preferences for working with an LLM. Fork this file to your own repo and edit the entries. Loaded by persona/personal-coding-reviewer + persona/personal-writing-companion at runtime.

**Industries**: cross_industry
**Capabilities**: retrieval
**Modalities**: text
**Freshness**: volatile
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/personal-preferences-pack/preferences.jsonl` | jsonl | — |

## Provenance

- **sources**: template — populate with your own preferences after forking
- **collected_through**: 2026-05-22
- **note**: This is a TEMPLATE. Replace the example records with your own.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/personal-preferences-template.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{personal-preferences-template_open_harness_hub,
  title  = {Personal preferences template (fork + edit)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/personal-preferences-template},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC0-1.0`. Hub component: `knowledge-pack/personal-preferences-template`.
