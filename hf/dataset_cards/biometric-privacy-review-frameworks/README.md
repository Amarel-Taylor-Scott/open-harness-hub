---
license: CC-BY-4.0
tags:
- ai_governance
- biometric-privacy-review
- expansion-v5
- experimental
- open-harness-hub
- privacy
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Biometric Privacy Review frameworks
---

# Biometric Privacy Review frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/biometric-privacy-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for biometric privacy review workflows.

**Industries**: privacy, ai_governance
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
| `data/biometric-privacy-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Biometric Privacy Review control checklist, Biometric Privacy Review evidence matrix, Biometric Privacy Review escalation playbook, Biometric Privacy Review benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/biometric-privacy-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{biometric-privacy-review-frameworks_open_harness_hub,
  title  = {Biometric Privacy Review frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/biometric-privacy-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/biometric-privacy-review-frameworks`.
