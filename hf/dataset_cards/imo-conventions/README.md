---
license: CC-BY-4.0
tags:
- beta
- imo
- maritime
- maritime.safety
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
pretty_name: IMO conventions (SOLAS / MARPOL / ISM / STCW / ISPS / MLC)
---

# IMO conventions (SOLAS / MARPOL / ISM / STCW / ISPS / MLC)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/imo-conventions` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite of IMO maritime safety + pollution + crew conventions.

**Industries**: maritime, maritime.safety
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/maritime-pack/imo-conventions.jsonl` | jsonl | — |

## Provenance

- **sources**: IMO SOLAS, MARPOL, ISM, STCW, ISPS, MLC 2006 (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/imo-conventions.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{imo-conventions_open_harness_hub,
  title  = {IMO conventions (SOLAS / MARPOL / ISM / STCW / ISPS / MLC)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/imo-conventions},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/imo-conventions`.
