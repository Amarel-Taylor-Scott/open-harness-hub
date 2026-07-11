---
license: CC-BY-4.0
tags:
- ai
- components
- cross_industry
- daily-factory
- evaluation
- experimental
- governance
- load-audit
- open-harness-hub
- planning
- resume
- software.devops
- stage-ledger
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Daily factory stage contracts
---

# Daily factory stage contracts

<!-- Generated from OpenHubForAI manifest `knowledge-pack/daily-factory-stage-contracts` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Stage contracts for resumable daily component factory runs, including expected summary files, prerequisites, and deterministic resume commands.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: planning, governance, evaluation
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `stage_contract`

## Files

| path | format | schema |
|---|---|---|
| `data/daily-factory-stage-contracts/stages.jsonl` | jsonl | — |

## Provenance

- **sources**: docs/codex/million-object-goal.md, docs/codex/object-factory-workflow.md, scripts/factory/daily_production_run.py, scripts/db/daily_partition_load_audit.py
- **collected_through**: 2026-05-26
- **collected_by**: OpenHubForAI contributors

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/daily-factory-stage-contracts.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{daily-factory-stage-contracts_open_harness_hub,
  title  = {Daily factory stage contracts},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/daily-factory-stage-contracts},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/daily-factory-stage-contracts`.
