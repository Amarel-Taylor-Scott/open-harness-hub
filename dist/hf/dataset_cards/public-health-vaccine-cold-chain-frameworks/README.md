---
license: CC-BY-4.0
tags:
- expansion-v7
- experimental
- healthcare.public_health
- logistics.cold_chain
- open-harness-hub
- public-health-vaccine-cold-chain
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Public Health Vaccine Cold Chain frameworks
---

# Public Health Vaccine Cold Chain frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/public-health-vaccine-cold-chain-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for public health vaccine cold chain workflows.

**Industries**: healthcare.public_health, logistics.cold_chain
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
| `data/public-health-vaccine-cold-chain/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Public Health Vaccine Cold Chain control checklist, Public Health Vaccine Cold Chain evidence matrix, Public Health Vaccine Cold Chain escalation playbook, Public Health Vaccine Cold Chain benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/public-health-vaccine-cold-chain-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{public-health-vaccine-cold-chain-frameworks_open_harness_hub,
  title  = {Public Health Vaccine Cold Chain frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/public-health-vaccine-cold-chain-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/public-health-vaccine-cold-chain-frameworks`.
