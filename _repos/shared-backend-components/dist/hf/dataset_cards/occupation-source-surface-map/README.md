---
license: CC-BY-4.0
tags:
- ai
- bls-ors
- cross_industry
- education
- esco
- experimental
- extraction
- governance
- hr
- job-descriptions
- occupations
- onet
- open-harness-hub
- planning
- procedure-objects
- retrieval
- work-atoms
task_categories:
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Occupation source surface map
---

# Occupation source surface map

<!-- Generated from OpenHubForAI manifest `knowledge-pack/occupation-source-surface-map` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Source surfaces for converting occupation taxonomies, job descriptions, public role classifications, and job requirements data into work atoms, questions, procedures, facts, and pipeline primitives.

**Industries**: ai, hr, education, cross_industry
**Capabilities**: retrieval, extraction, planning, governance
**Modalities**: text, structured
**Freshness**: volatile
**Trust boundary**: external

## Content types (leaf vocabulary)

- `occupation_source_surface`
- `work_atom_schema`
- `source_mapping`

## Files

| path | format | schema |
|---|---|---|
| `data/occupation-source-surface-map/surfaces.jsonl` | jsonl | — |

## Provenance

- **sources**: O*NET, ESCO, BLS Occupational Requirements Survey, OpenHubForAI occupation-to-procedure plan
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: source map only; no applicant or employer PII

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/occupation-source-surface-map.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{occupation-source-surface-map_open_harness_hub,
  title  = {Occupation source surface map},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/occupation-source-surface-map},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/occupation-source-surface-map`.
