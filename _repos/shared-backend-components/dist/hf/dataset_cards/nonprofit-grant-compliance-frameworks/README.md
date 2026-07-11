---
license: CC-BY-4.0
tags:
- experimental
- nonprofit
- nonprofit-grant-compliance
- open-harness-hub
- retrieval
- synthetic-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Nonprofit Grant Compliance frameworks
---

# Nonprofit Grant Compliance frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/nonprofit-grant-compliance-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference pack covering Uniform Guidance allowable costs, subrecipient monitoring, restricted-fund accounting, grant reporting calendar.

**Industries**: nonprofit
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `policy_summary`

## Files

| path | format | schema |
|---|---|---|
| `data/nonprofit-grant-compliance/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Uniform Guidance allowable costs, subrecipient monitoring, restricted-fund accounting, grant reporting calendar
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/nonprofit-grant-compliance-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{nonprofit-grant-compliance-frameworks_open_harness_hub,
  title  = {Nonprofit Grant Compliance frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/nonprofit-grant-compliance-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/nonprofit-grant-compliance-frameworks`.
