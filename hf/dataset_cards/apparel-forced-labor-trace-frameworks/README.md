---
license: CC-BY-4.0
tags:
- apparel-forced-labor-trace
- esg.modern_slavery
- expansion-v4
- experimental
- open-harness-hub
- retrieval
- supply_chain.due_diligence
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Apparel Forced Labor Trace frameworks
---

# Apparel Forced Labor Trace frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/apparel-forced-labor-trace-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for apparel forced labor trace review, evidence, escalation, and benchmarking.

**Industries**: esg.modern_slavery, supply_chain.due_diligence
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
| `data/apparel-forced-labor-trace/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Apparel Forced Labor Trace control checklist, Apparel Forced Labor Trace evidence matrix, Apparel Forced Labor Trace escalation playbook, Apparel Forced Labor Trace benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/apparel-forced-labor-trace-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{apparel-forced-labor-trace-frameworks_open_harness_hub,
  title  = {Apparel Forced Labor Trace frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/apparel-forced-labor-trace-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/apparel-forced-labor-trace-frameworks`.
