---
license: CC-BY-4.0
tags:
- editorial-style-compliance
- expansion-v7
- experimental
- media.editorial
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
pretty_name: Editorial Style Compliance frameworks
---

# Editorial Style Compliance frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/editorial-style-compliance-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for editorial style compliance workflows.

**Industries**: media.editorial, media.factcheck
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
| `data/editorial-style-compliance/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Editorial Style Compliance control checklist, Editorial Style Compliance evidence matrix, Editorial Style Compliance escalation playbook, Editorial Style Compliance benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/editorial-style-compliance-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{editorial-style-compliance-frameworks_open_harness_hub,
  title  = {Editorial Style Compliance frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/editorial-style-compliance-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/editorial-style-compliance-frameworks`.
