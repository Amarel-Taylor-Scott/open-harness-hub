---
license: CC-BY-4.0
tags:
- experimental
- manufacturing
- manufacturing-nc-capa
- manufacturing.qa
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
pretty_name: Manufacturing NC CAPA frameworks
---

# Manufacturing NC CAPA frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/manufacturing-nc-capa-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference pack covering ISO 9001 nonconformity control, IATF 16949 corrective action discipline, 8D problem solving, statistical process control evidence.

**Industries**: manufacturing, manufacturing.qa
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
| `data/manufacturing-nc-capa/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: ISO 9001 nonconformity control, IATF 16949 corrective action discipline, 8D problem solving, statistical process control evidence
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/manufacturing-nc-capa-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{manufacturing-nc-capa-frameworks_open_harness_hub,
  title  = {Manufacturing NC CAPA frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/manufacturing-nc-capa-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/manufacturing-nc-capa-frameworks`.
