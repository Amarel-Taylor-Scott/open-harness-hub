---
name: duplicate-collapse-report
description: Detect duplicate primary-key collapse in staged component row families
  and distinguish shared reference rows from critical component candidate collisions.
when_to_use: 'Pipeline kind: research_web.duplicate_collapse_report.'
---

# Duplicate collapse report

Reports staged row-family duplicate collapse before load audit, index coverage repair, promotion readiness, or Postgres loading.

## Task

Detect duplicate primary-key collapse in staged component row families and distinguish shared reference rows from critical component candidate collisions.

## Steps

1. **load-duplicate-collapse-patterns** — `knowledge_pack` → `knowledge-pack/duplicate-collapse-report-patterns`
2. **report-duplicate-collapse** — `tool` → `tool/duplicate-collapse-reporter`
3. **route-conflicts** — `tool` → `tool/object-factory-job-router`

## Defaults

- **knowledge_packs**: `knowledge-pack/duplicate-collapse-report-patterns`

## Success criteria

- deterministic `$.duplicate_collapse_report.counts.row_families` >= `10`
- deterministic `$.duplicate_collapse_report.counts.conflicting_duplicate_key_groups` >= `0`
- semantic must_cover ['primary key', 'row family', 'ID source', 'conflicting duplicate', 'critical component rows', 'no database side effects'] against `$.duplicate_collapse_report`

## Provenance

- Hub component: `pipeline/duplicate-collapse-report` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
