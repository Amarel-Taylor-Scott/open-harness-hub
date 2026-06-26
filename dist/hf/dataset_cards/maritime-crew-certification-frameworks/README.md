---
license: CC-BY-4.0
tags:
- expansion-v7
- experimental
- maritime-crew-certification
- maritime.safety
- open-harness-hub
- retrieval
- transportation.maritime
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Maritime Crew Certification frameworks
---

# Maritime Crew Certification frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/maritime-crew-certification-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for maritime crew certification workflows.

**Industries**: maritime.safety, transportation.maritime
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
| `data/maritime-crew-certification/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Maritime Crew Certification control checklist, Maritime Crew Certification evidence matrix, Maritime Crew Certification escalation playbook, Maritime Crew Certification benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/maritime-crew-certification-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{maritime-crew-certification-frameworks_open_harness_hub,
  title  = {Maritime Crew Certification frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/maritime-crew-certification-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/maritime-crew-certification-frameworks`.
