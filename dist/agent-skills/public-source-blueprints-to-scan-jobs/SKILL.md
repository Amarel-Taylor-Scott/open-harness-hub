---
name: public-source-blueprints-to-scan-jobs
description: Emit queue-ready scan jobs and shard manifests from public-source blueprints,
  with source governance and excluded-scope policy attached to every job.
when_to_use: 'Pipeline kind: research_web.public_source_scan_job_emission.'
---

# Public source blueprints to scan jobs

Turns governed public-source blueprints into resumable object-factory scan jobs that can be consumed by containerized workers without embedding scraped source bodies in the catalog.

## Task

Emit queue-ready scan jobs and shard manifests from public-source blueprints, with source governance and excluded-scope policy attached to every job.

## Steps

1. **govern-public-source-blueprint-batch** — `tool` → `tool/source-record-governance-router`
2. **normalize-blueprints** — `tool` → `tool/public-source-blueprint-normalizer`
3. **emit-scan-jobs** — `tool` → `tool/public-source-scan-job-emitter`
4. **route-emitted-jobs** — `tool` → `tool/object-factory-job-router`

## Defaults

- **knowledge_packs**: `knowledge-pack/public-source-blueprint-catalog`, `knowledge-pack/public-source-scan-job-patterns`

## Success criteria

- deterministic `$.job_count` > `0`
- semantic must_cover ['source_discovery', 'source_snapshot', 'page_to_markdown', 'source_ingest', 'entity_linking', 'fuzzy_dedupe', 'dedupe_index', 'publish_review'] against `$.job_counts_by_type`

## Provenance

- Hub component: `pipeline/public-source-blueprints-to-scan-jobs` v0.1.0
- License: `MIT`
- Industry: automotive, energy, manufacturing, construction, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
