---
license: CC-BY-4.0
tags:
- clinical-trial-protocol-deviation
- expansion-v4
- experimental
- healthcare.clinical
- open-harness-hub
- pharma.clinical
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Clinical Trial Protocol Deviation frameworks
---

# Clinical Trial Protocol Deviation frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/clinical-trial-protocol-deviation-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for clinical trial protocol deviation review, evidence, escalation, and benchmarking.

**Industries**: pharma.clinical, healthcare.clinical
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
| `data/clinical-trial-protocol-deviation/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Clinical Trial Protocol Deviation control checklist, Clinical Trial Protocol Deviation evidence matrix, Clinical Trial Protocol Deviation escalation playbook, Clinical Trial Protocol Deviation benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/clinical-trial-protocol-deviation-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{clinical-trial-protocol-deviation-frameworks_open_harness_hub,
  title  = {Clinical Trial Protocol Deviation frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/clinical-trial-protocol-deviation-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/clinical-trial-protocol-deviation-frameworks`.
