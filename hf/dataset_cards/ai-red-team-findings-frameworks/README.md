---
license: CC-BY-4.0
tags:
- ai
- ai-red-team-findings
- expansion-v5
- experimental
- open-harness-hub
- retrieval
- security.offensive
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: AI Red Team Findings frameworks
---

# AI Red Team Findings frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/ai-red-team-findings-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for ai red team findings workflows.

**Industries**: ai, security.offensive
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
| `data/ai-red-team-findings/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: AI Red Team Findings control checklist, AI Red Team Findings evidence matrix, AI Red Team Findings escalation playbook, AI Red Team Findings benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/ai-red-team-findings-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{ai-red-team-findings-frameworks_open_harness_hub,
  title  = {AI Red Team Findings frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/ai-red-team-findings-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/ai-red-team-findings-frameworks`.
