---
license: CC-BY-4.0
tags:
- experimental
- gov-foia-exemptions
- government
- government.foia
- open-harness-hub
- privacy
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
pretty_name: Government FOIA Exemptions frameworks
---

# Government FOIA Exemptions frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/gov-foia-exemptions-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference pack covering FOIA nine exemptions, segregability requirement, privacy balancing test, Vaughn index preparation.

**Industries**: government, government.foia, privacy
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
| `data/gov-foia-exemptions/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: FOIA nine exemptions, segregability requirement, privacy balancing test, Vaughn index preparation
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/gov-foia-exemptions-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{gov-foia-exemptions-frameworks_open_harness_hub,
  title  = {Government FOIA Exemptions frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/gov-foia-exemptions-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/gov-foia-exemptions-frameworks`.
