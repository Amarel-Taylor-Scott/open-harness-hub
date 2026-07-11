---
name: specialized-model-signals-to-scan-jobs
description: Emit queue-ready model-card scan jobs and shard manifests from specialized
  model signal rows, with governance and excluded-scope policy attached to every job.
when_to_use: 'Pipeline kind: research_web.specialized_model_card_scan_job_emission.'
---

# Specialized model signals to scan jobs

Turns specialized model signal rows into resumable object-factory jobs that mine model-card context into reusable primitive candidates without downloading model weights.

## Task

Emit queue-ready model-card scan jobs and shard manifests from specialized model signal rows, with governance and excluded-scope policy attached to every job.

## Steps

1. **govern-specialized-model-signal-batch** — `tool` → `tool/source-record-governance-router`
2. **emit-model-card-scan-jobs** — `tool` → `tool/specialized-model-card-scan-job-emitter`
3. **route-emitted-model-card-jobs** — `tool` → `tool/object-factory-job-router`

## Defaults

- **knowledge_packs**: `knowledge-pack/specialized-model-signal-surfaces`, `knowledge-pack/specialized-model-card-scan-job-patterns`

## Success criteria

- deterministic `$.job_count` > `0`
- semantic must_cover ['model_repo_discovery', 'model_card_snapshot', 'model_metadata_parse', 'task_context_normalize', 'dataset_eval_linking', 'entity_linking', 'fuzzy_dedupe', 'primitive_index', 'publish_review'] against `$.job_counts_by_type`

## Provenance

- Hub component: `pipeline/specialized-model-signals-to-scan-jobs` v0.1.0
- License: `MIT`
- Industry: healthcare, finance, legal, software.devops, media, security, privacy, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
