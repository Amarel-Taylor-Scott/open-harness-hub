---
name: source-surfaces-to-scan-partitions
description: Plan additive source-surface scan partitions and route them into public-source
  scan jobs without storing raw source bodies in the public catalog.
when_to_use: 'Pipeline kind: research_web.source_surface_partitioning.'
---

# Source surfaces to scan partitions

Turns high-value source-surface backlog rows into resumable partitions, public-source blueprints, and queue-ready scan jobs for the object factory.

## Task

Plan additive source-surface scan partitions and route them into public-source scan jobs without storing raw source bodies in the public catalog.

## Steps

1. **govern-source-surface-backlog** — `tool` → `tool/source-record-governance-router`
2. **plan-source-surface-partitions** — `tool` → `tool/source-surface-partition-planner`
3. **emit-public-source-scan-jobs** — `tool` → `tool/public-source-scan-job-emitter`
4. **route-jobs-to-container-workers** — `tool` → `tool/object-factory-job-router`

## Defaults

- **knowledge_packs**: `knowledge-pack/source-surface-partition-patterns`, `knowledge-pack/public-source-scan-job-patterns`

## Success criteria

- deterministic `$.partition_count` > `0`
- semantic must_cover ['source governance', 'resume cursor', 'entity linking', 'fuzzy dedupe', 'index record', 'review routing'] against `$.source_surface_scan_partitions`

## Provenance

- Hub component: `pipeline/source-surfaces-to-scan-partitions` v0.1.0
- License: `MIT`
- Industry: government, software, media, construction, energy, finance, healthcare, cross_industry
- Full source manifest: see `references/manifest.yaml`
