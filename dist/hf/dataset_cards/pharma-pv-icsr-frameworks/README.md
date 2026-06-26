---
license: CC-BY-4.0
tags:
- experimental
- healthcare.pharmacy
- open-harness-hub
- pharma
- pharma-pv-icsr
- pharma.pv
- retrieval
- synthetic-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Pharma PV ICSR frameworks
---

# Pharma PV ICSR frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/pharma-pv-icsr-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference pack covering ICH E2B ICSR minimum criteria, serious adverse event assessment, expedited reporting clocks, MedDRA coding discipline.

**Industries**: pharma, pharma.pv, healthcare.pharmacy
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `policy_summary`

## Files

| path | format | schema |
|---|---|---|
| `data/pharma-pv-icsr/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: ICH E2B ICSR minimum criteria, serious adverse event assessment, expedited reporting clocks, MedDRA coding discipline
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/pharma-pv-icsr-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{pharma-pv-icsr-frameworks_open_harness_hub,
  title  = {Pharma PV ICSR frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/pharma-pv-icsr-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/pharma-pv-icsr-frameworks`.
