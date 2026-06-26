---
license: CC-BY-4.0
tags:
- expansion-v5
- experimental
- legal.compliance
- open-harness-hub
- privacy
- records-retention-disposition
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Records Retention Disposition frameworks
---

# Records Retention Disposition frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/records-retention-disposition-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for records retention disposition workflows.

**Industries**: legal.compliance, privacy
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`
- `evidence_matrix`
- `benchmark_context`

## Files

| path | format | schema |
|---|---|---|
| `data/records-retention-disposition/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Records Retention Disposition control checklist, Records Retention Disposition evidence matrix, Records Retention Disposition escalation playbook, Records Retention Disposition benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/records-retention-disposition-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{records-retention-disposition-frameworks_open_harness_hub,
  title  = {Records Retention Disposition frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/records-retention-disposition-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/records-retention-disposition-frameworks`.
