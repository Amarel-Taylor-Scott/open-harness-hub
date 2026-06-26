---
license: CC-BY-4.0
tags:
- automotive
- construction
- cross_industry
- energy
- evaluation
- experimental
- extraction
- governance
- government
- manufacturing
- object-factory
- open-harness-hub
- public-sources
- queues
- retrieval
- routing
- scan-jobs
- worker-shards
task_categories:
- text-classification
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Public source scan job patterns
---

# Public source scan job patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/public-source-scan-job-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Patterns for expanding public source blueprints into queue-ready object-factory scan, snapshot, conversion, ingest, entity-linking, dedupe, index, and review jobs.

**Industries**: automotive, energy, manufacturing, construction, government, cross_industry
**Capabilities**: retrieval, extraction, governance, routing, evaluation
**Modalities**: text, image, structured
**Freshness**: volatile
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `object_factory_job_pattern`
- `public_source_scan_job`
- `worker_shard_manifest`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/public-source-scan-job-patterns/rows.jsonl` | jsonl | public-source-scan-job-pattern |

## Provenance

- **sources**: OpenHubForAI public source scan job emitter, OpenHubForAI object factory job schema
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: Job pattern metadata only; no scraped source bodies or private data.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/public-source-scan-job-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{public-source-scan-job-patterns_open_harness_hub,
  title  = {Public source scan job patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/public-source-scan-job-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/public-source-scan-job-patterns`.
