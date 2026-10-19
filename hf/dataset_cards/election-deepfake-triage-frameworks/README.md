---
license: CC-BY-4.0
tags:
- election-deepfake-triage
- election_integrity.deepfake
- expansion-v4
- experimental
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
pretty_name: Election Deepfake Triage frameworks
---

# Election Deepfake Triage frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/election-deepfake-triage-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for election deepfake triage review, evidence, escalation, and benchmarking.

**Industries**: election_integrity.deepfake, media.factcheck
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
| `data/election-deepfake-triage/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Election Deepfake Triage control checklist, Election Deepfake Triage evidence matrix, Election Deepfake Triage escalation playbook, Election Deepfake Triage benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/election-deepfake-triage-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{election-deepfake-triage-frameworks_open_harness_hub,
  title  = {Election Deepfake Triage frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/election-deepfake-triage-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/election-deepfake-triage-frameworks`.
