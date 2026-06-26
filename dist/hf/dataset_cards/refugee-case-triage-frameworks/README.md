---
license: CC-BY-4.0
tags:
- expansion-v4
- experimental
- humanitarian.refugee
- legal.immigration
- open-harness-hub
- refugee-case-triage
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Refugee Case Triage frameworks
---

# Refugee Case Triage frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/refugee-case-triage-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for refugee case triage review, evidence, escalation, and benchmarking.

**Industries**: humanitarian.refugee, legal.immigration
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
| `data/refugee-case-triage/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Refugee Case Triage control checklist, Refugee Case Triage evidence matrix, Refugee Case Triage escalation playbook, Refugee Case Triage benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/refugee-case-triage-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{refugee-case-triage-frameworks_open_harness_hub,
  title  = {Refugee Case Triage frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/refugee-case-triage-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/refugee-case-triage-frameworks`.
