---
license: CC-BY-4.0
tags:
- beta
- election-integrity
- election_integrity
- media
- media.factcheck
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
pretty_name: Election integrity frameworks (EAC / CISA / DHS / C2PA)
---

# Election integrity frameworks (EAC / CISA / DHS / C2PA)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/election-integrity-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite — EAC election standards + CISA election infrastructure + DHS election cyber + C2PA Content Credentials + ACT methodology.

**Industries**: election_integrity, media, media.factcheck
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/election-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: EAC Voluntary Voting System Guidelines (composite), CISA election security resources (composite), DHS CISA #Protect2024 (composite), C2PA spec 1.x (composite), ACT on Election Integrity methodology (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/election-integrity-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{election-integrity-frameworks_open_harness_hub,
  title  = {Election integrity frameworks (EAC / CISA / DHS / C2PA)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/election-integrity-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/election-integrity-frameworks`.
