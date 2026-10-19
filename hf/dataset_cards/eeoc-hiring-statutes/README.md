---
license: CC-BY-4.0
tags:
- ada
- adea
- beta
- compliance
- eeoc
- gina
- hr
- hr.hiring
- open-harness-hub
- pwfa
- retrieval
- title-vii
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: EEOC hiring statutes pack (Title VII / ADA / ADEA / GINA / PWFA)
---

# EEOC hiring statutes pack (Title VII / ADA / ADEA / GINA / PWFA)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/eeoc-hiring-statutes` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite educational reference of the federal anti-discrimination
hiring statutes administered by the EEOC + OFCCP.

**Industries**: hr, hr.hiring, compliance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/hr-pack/statutes.jsonl` | jsonl | — |

## Provenance

- **sources**: EEOC enforcement guidance (composite), 29 CFR 1604 (sex discrimination guidelines, composite), 29 CFR 1630 (ADA, composite), 29 CFR 1635 (GINA, composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/eeoc-hiring-statutes.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{eeoc-hiring-statutes_open_harness_hub,
  title  = {EEOC hiring statutes pack (Title VII / ADA / ADEA / GINA / PWFA)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/eeoc-hiring-statutes},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/eeoc-hiring-statutes`.
