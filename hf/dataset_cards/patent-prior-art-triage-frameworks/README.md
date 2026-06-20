---
license: CC-BY-4.0
tags:
- expansion-v5
- experimental
- legal.ip
- open-harness-hub
- patent-prior-art-triage
- retrieval
- scientific_research.physical
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Patent Prior Art Triage frameworks
---

# Patent Prior Art Triage frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/patent-prior-art-triage-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for patent prior art triage workflows.

**Industries**: legal.ip, scientific_research.physical
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
| `data/patent-prior-art-triage/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Patent Prior Art Triage control checklist, Patent Prior Art Triage evidence matrix, Patent Prior Art Triage escalation playbook, Patent Prior Art Triage benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/patent-prior-art-triage-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{patent-prior-art-triage-frameworks_open_harness_hub,
  title  = {Patent Prior Art Triage frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/patent-prior-art-triage-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/patent-prior-art-triage-frameworks`.
