---
license: CC-BY-4.0
tags:
- ai
- classification
- cross_industry
- dedupe
- experimental
- extraction
- governance
- indexing
- llm-routing
- object-factory
- open-harness-hub
- privacy
- routing
- software.devops
- summarization
- verification
- workers
task_categories:
- summarization
- text-classification
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Object factory worker patterns
---

# Object factory worker patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/object-factory-worker-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reference worker patterns for converting source material into privacy-screened, verified, labeled, deduplicated Open Harness Hub objects.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: extraction, summarization, classification, verification, governance, routing
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `object-factory-worker-pattern`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/object-factory-worker-patterns/workers.jsonl` | jsonl | schemas/object-factory-worker.schema.json |

## Provenance

- **sources**: Open Harness Hub architecture notes
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Synthetic worker patterns only; no real PII or tenant data.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/object-factory-worker-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{object-factory-worker-patterns_open_harness_hub,
  title  = {Object factory worker patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/object-factory-worker-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/object-factory-worker-patterns`.
