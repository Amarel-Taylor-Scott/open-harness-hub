---
license: CC-BY-4.0
tags:
- expansion-v6
- experimental
- insurance.claims
- maritime-cargo-claims
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
pretty_name: Maritime Cargo Claims frameworks
---

# Maritime Cargo Claims frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/maritime-cargo-claims-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for maritime cargo claims workflows.

**Industries**: maritime.safety, insurance.claims
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
| `data/maritime-cargo-claims/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Maritime Cargo Claims control checklist, Maritime Cargo Claims evidence matrix, Maritime Cargo Claims escalation playbook, Maritime Cargo Claims benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/maritime-cargo-claims-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{maritime-cargo-claims-frameworks_open_harness_hub,
  title  = {Maritime Cargo Claims frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/maritime-cargo-claims-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/maritime-cargo-claims-frameworks`.
