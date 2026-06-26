---
license: CC-BY-4.0
tags:
- aviation-sms-risk-register
- aviation.maintenance
- aviation.safety
- expansion-v7
- experimental
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
pretty_name: Aviation SMS Risk Register frameworks
---

# Aviation SMS Risk Register frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/aviation-sms-risk-register-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for aviation sms risk register workflows.

**Industries**: aviation.safety, aviation.maintenance
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
| `data/aviation-sms-risk-register/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Aviation SMS Risk Register control checklist, Aviation SMS Risk Register evidence matrix, Aviation SMS Risk Register escalation playbook, Aviation SMS Risk Register benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/aviation-sms-risk-register-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{aviation-sms-risk-register-frameworks_open_harness_hub,
  title  = {Aviation SMS Risk Register frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/aviation-sms-risk-register-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/aviation-sms-risk-register-frameworks`.
