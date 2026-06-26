---
license: CC-BY-4.0
tags:
- experimental
- legal
- legal-ip-trademark
- legal.ip
- open-harness-hub
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
pretty_name: Legal IP Trademark frameworks
---

# Legal IP Trademark frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/legal-ip-trademark-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference pack covering likelihood of confusion factors, Nice classification goods/services, descriptiveness and genericness review, common-law search evidence.

**Industries**: legal, legal.ip
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
| `data/legal-ip-trademark/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: likelihood of confusion factors, Nice classification goods/services, descriptiveness and genericness review, common-law search evidence
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/legal-ip-trademark-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{legal-ip-trademark-frameworks_open_harness_hub,
  title  = {Legal IP Trademark frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/legal-ip-trademark-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/legal-ip-trademark-frameworks`.
