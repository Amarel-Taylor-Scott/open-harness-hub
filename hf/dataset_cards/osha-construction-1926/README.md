---
license: CC-BY-4.0
tags:
- beta
- construction
- construction.safety
- open-harness-hub
- osha
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: OSHA 29 CFR 1926 (Construction) + ANSI Z10 + Focus Four
---

# OSHA 29 CFR 1926 (Construction) + ANSI Z10 + Focus Four

<!-- Generated from Open Harness Hub manifest `knowledge-pack/osha-construction-1926` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite extracts of OSHA 1926 subparts + Focus Four + competent-person + ANSI Z10.

**Industries**: construction, construction.safety
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/construction-pack/osha-1926.jsonl` | jsonl | — |

## Provenance

- **sources**: OSHA 29 CFR 1926 (composite), ANSI Z10 (composite), OSHA Focus Four resources (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/osha-construction-1926.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{osha-construction-1926_open_harness_hub,
  title  = {OSHA 29 CFR 1926 (Construction) + ANSI Z10 + Focus Four},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/osha-construction-1926},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/osha-construction-1926`.
