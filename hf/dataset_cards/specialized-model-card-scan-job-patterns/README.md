---
license: CC-BY-4.0
tags:
- classification
- cross_industry
- embedding
- evaluation
- experimental
- extraction
- finance
- governance
- government
- healthcare
- huggingface
- legal
- media
- model-cards
- object-factory
- open-harness-hub
- privacy
- queue-ready
- retrieval
- routing
- security
- software.devops
- specialized-models
- worker-jobs
task_categories:
- sentence-similarity
- text-classification
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Specialized model card scan job patterns
---

# Specialized model card scan job patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/specialized-model-card-scan-job-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Queue-stage patterns for turning task-specific model cards and model repositories into governed object-factory jobs and reusable primitive candidates.

**Industries**: healthcare, finance, legal, software.devops, media, security, privacy, government, cross_industry
**Capabilities**: retrieval, extraction, classification, evaluation, routing, governance, embedding
**Modalities**: text, image, structured
**Freshness**: volatile
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `object_factory_job_type`
- `scan_lifecycle`
- `review_route`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/specialized-model-card-scan-job-patterns/job-types.jsonl` | jsonl | — |

## Provenance

- **sources**: catalog/knowledge-packs/data/specialized-model-signal-surfaces/models.jsonl, scripts/factory/specialized_model_card_scan_jobs.py
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: public model metadata only; no model weights, private training data, or PII copied

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/specialized-model-card-scan-job-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{specialized-model-card-scan-job-patterns_open_harness_hub,
  title  = {Specialized model card scan job patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/specialized-model-card-scan-job-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/specialized-model-card-scan-job-patterns`.
