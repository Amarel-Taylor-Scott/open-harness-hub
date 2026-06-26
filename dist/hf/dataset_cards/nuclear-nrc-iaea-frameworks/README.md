---
license: CC-BY-4.0
tags:
- beta
- nuclear
- nuclear.power
- nuclear.security
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
pretty_name: Nuclear safety frameworks (NRC 10 CFR + IAEA + INPO)
---

# Nuclear safety frameworks (NRC 10 CFR + IAEA + INPO)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/nuclear-nrc-iaea-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

10 CFR 20/50/73 + IAEA INFCIRC + INPO + ROP significance determination.

**Industries**: nuclear, nuclear.power, nuclear.security
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/nuclear-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: 10 CFR Parts 20/50/73/74 (composite), IAEA INFCIRC/153 + INFCIRC/225 (composite), INPO AP-913 + AP-928 (composite), NRC Reactor Oversight Process (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/nuclear-nrc-iaea-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{nuclear-nrc-iaea-frameworks_open_harness_hub,
  title  = {Nuclear safety frameworks (NRC 10 CFR + IAEA + INPO)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/nuclear-nrc-iaea-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/nuclear-nrc-iaea-frameworks`.
