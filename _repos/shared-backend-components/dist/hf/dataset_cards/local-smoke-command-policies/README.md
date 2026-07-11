---
license: CC-BY-4.0
tags:
- ai
- approval-gate
- command-ledger
- components
- cross_industry
- evaluation
- experimental
- governance
- open-harness-hub
- pgvector
- postgres
- smoke-test
- software.devops
- verification
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Local smoke command policies
---

# Local smoke command policies

<!-- Generated from OpenHubForAI manifest `knowledge-pack/local-smoke-command-policies` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Command classification policies for local Docker pgvector smoke plans, including approval requirements for Docker, psql, and audit commands.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, evaluation, verification
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `command_policy`

## Files

| path | format | schema |
|---|---|---|
| `data/local-smoke-command-policies/policies.jsonl` | jsonl | — |

## Provenance

- **sources**: scripts/db/component_local_postgres_smoke_plan.py, docs/architecture/model-runtime-training-and-federated-sharing-components.md
- **collected_through**: 2026-05-26
- **collected_by**: OpenHubForAI contributors

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/local-smoke-command-policies.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{local-smoke-command-policies_open_harness_hub,
  title  = {Local smoke command policies},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/local-smoke-command-policies},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/local-smoke-command-policies`.
