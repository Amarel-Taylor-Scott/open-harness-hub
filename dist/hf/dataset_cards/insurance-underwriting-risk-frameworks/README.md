---
license: CC-BY-4.0
tags:
- expansion-v4
- experimental
- insurance-underwriting-risk
- insurance.underwriting
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
pretty_name: Insurance Underwriting Risk frameworks
---

# Insurance Underwriting Risk frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/insurance-underwriting-risk-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for insurance underwriting risk review, evidence, escalation, and benchmarking.

**Industries**: insurance.underwriting
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
| `data/insurance-underwriting-risk/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Insurance Underwriting Risk control checklist, Insurance Underwriting Risk evidence matrix, Insurance Underwriting Risk escalation playbook, Insurance Underwriting Risk benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/insurance-underwriting-risk-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{insurance-underwriting-risk-frameworks_open_harness_hub,
  title  = {Insurance Underwriting Risk frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/insurance-underwriting-risk-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/insurance-underwriting-risk-frameworks`.
