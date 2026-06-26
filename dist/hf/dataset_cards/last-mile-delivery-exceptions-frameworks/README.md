---
license: CC-BY-4.0
tags:
- experimental
- last-mile-delivery-exceptions
- logistics.last_mile
- open-harness-hub
- retail.support
- retrieval
- use-case-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Last Mile Delivery Exceptions frameworks
---

# Last Mile Delivery Exceptions frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/last-mile-delivery-exceptions-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite operational reference pack for last mile delivery exceptions use cases.

**Industries**: logistics.last_mile, retail.support
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`

## Files

| path | format | schema |
|---|---|---|
| `data/last-mile-delivery-exceptions/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: proof-of-delivery evidence review, carrier exception coding, customer refund decision matrix, address correction and geocode review
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/last-mile-delivery-exceptions-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{last-mile-delivery-exceptions-frameworks_open_harness_hub,
  title  = {Last Mile Delivery Exceptions frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/last-mile-delivery-exceptions-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/last-mile-delivery-exceptions-frameworks`.
