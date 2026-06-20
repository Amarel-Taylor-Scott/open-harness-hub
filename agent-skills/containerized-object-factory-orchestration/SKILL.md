---
name: containerized-object-factory-orchestration
description: Split Open Harness Hub object generation into parallel container worker
  lanes with source governance, shard leasing, enrichment, validation, promotion,
  warehouse export, and prompt-prefix cache normalization.
when_to_use: 'Pipeline kind: research_web.object_factory_worker_fleet.'
---

# Containerized object factory orchestration

Plans and audits a horizontally scalable worker fleet for source discovery, scraping, spidering, repository/workflow mining, enrichment, embedding, verification, promotion, warehouse export, and prompt-prefix cache savings.

## Task

Split Open Harness Hub object generation into parallel container worker lanes with source governance, shard leasing, enrichment, validation, promotion, warehouse export, and prompt-prefix cache normalization.

## Steps

1. **source-governance** — `tool` → `tool/source-record-governance-router`
2. **plan-shards** — `tool` → `tool/container-worker-shard-planner`
3. **route-worker-jobs** — `tool` → `tool/object-factory-job-router`
4. **normalize-prompt-prefix** — `tool` → `tool/prompt-prefix-cache-normalizer`
5. **export-cold-tier-plan** — `tool` → `tool/bigquery-cold-tier-export-planner`
6. **merge-audit** — `tool` → `tool/worker-output-merge-auditor`

## Defaults

- **knowledge_packs**: `knowledge-pack/containerized-worker-orchestration-patterns`, `knowledge-pack/hybrid-postgres-bigquery-hosting-patterns`, `knowledge-pack/trajectory-fragment-cache-patterns`

## Success criteria

- semantic must_cover ['discovery workers', 'spider workers', 'parallel enrichment', 'merge audit', 'warehouse export'] against `$.shard_plan`
- semantic must_cover ['stable prompt prefix', 'schema block', 'tool signatures', 'variable content late', 'cost savings'] against `$.prompt_cache_profile`
- deterministic `$.merge_audit` is_truthy `True`

## Provenance

- Hub component: `pipeline/containerized-object-factory-orchestration` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
