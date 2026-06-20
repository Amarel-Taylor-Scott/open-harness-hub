---
license: CC-BY-4.0
tags:
- charity-donor-restriction
- expansion-v3
- experimental
- nonprofit
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
pretty_name: Charity Donor Restriction frameworks
---

# Charity Donor Restriction frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/charity-donor-restriction-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for charity donor restriction reviews, including evidence, escalation, and remediation controls.

**Industries**: nonprofit
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`
- `evidence_matrix`

## Files

| path | format | schema |
|---|---|---|
| `data/charity-donor-restriction/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Charity Donor Restriction control checklist, Charity Donor Restriction evidence matrix, Charity Donor Restriction escalation playbook, Charity Donor Restriction remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/charity-donor-restriction-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{charity-donor-restriction-frameworks_open_harness_hub,
  title  = {Charity Donor Restriction frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/charity-donor-restriction-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/charity-donor-restriction-frameworks`.
