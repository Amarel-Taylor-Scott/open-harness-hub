---
license: CC-BY-4.0
tags:
- cold-chain-pharma-release
- expansion-v5
- experimental
- logistics.cold_chain
- open-harness-hub
- pharma.gxp
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Cold Chain Pharma Release frameworks
---

# Cold Chain Pharma Release frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/cold-chain-pharma-release-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for cold chain pharma release workflows.

**Industries**: logistics.cold_chain, pharma.gxp
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
| `data/cold-chain-pharma-release/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Cold Chain Pharma Release control checklist, Cold Chain Pharma Release evidence matrix, Cold Chain Pharma Release escalation playbook, Cold Chain Pharma Release benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/cold-chain-pharma-release-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{cold-chain-pharma-release-frameworks_open_harness_hub,
  title  = {Cold Chain Pharma Release frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/cold-chain-pharma-release-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/cold-chain-pharma-release-frameworks`.
