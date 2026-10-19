---
name: public-source-scan-jobs-to-replay-partitions
description: Replay public-source scan jobs into additive partition manifests and
  checkpoints without storing source bodies, then audit the generated partitions for
  later bulk-load and index replay.
when_to_use: 'Pipeline kind: research_web.public_source_job_replay_partitions.'
---

# Public source scan jobs to replay partitions

Consumes emitted public-source scan jobs and produces resumable run records, checkpoints, and partition manifests that prepare later container workers and Postgres/pgvector bulk loads.

## Task

Replay public-source scan jobs into additive partition manifests and checkpoints without storing source bodies, then audit the generated partitions for later bulk-load and index replay.

## Steps

1. **govern-scan-job-batch** — `tool` → `tool/source-record-governance-router`
2. **replay-scan-jobs** — `tool` → `tool/public-source-job-replay-runner`
3. **audit-replay-partitions** — `tool` → `tool/worker-output-merge-auditor`

## Defaults

- **knowledge_packs**: `knowledge-pack/public-source-scan-job-patterns`, `knowledge-pack/public-source-job-replay-patterns`

## Success criteria

- deterministic `$.partition_count` > `0`
- semantic must_cover ['job id', 'input hash', 'checkpoint', 'output pointer', 'privacy policy', 'partition manifest'] against `$.job_run_records`

## Provenance

- Hub component: `pipeline/public-source-scan-jobs-to-replay-partitions` v0.1.0
- License: `MIT`
- Industry: automotive, energy, manufacturing, construction, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
