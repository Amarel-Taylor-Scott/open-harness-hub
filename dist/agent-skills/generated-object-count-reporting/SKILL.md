---
name: generated-object-count-reporting
description: Report OpenHubForAI scale metrics without confusing YAML manifests with
  generated database objects.
when_to_use: 'Pipeline kind: evaluate.'
---

# Generated object count reporting

Separates curated manifest count, staged JSONL rows, and canonical Postgres object rows before reporting progress toward million-object scale.

## Task

Report OpenHubForAI scale metrics without confusing YAML manifests with generated database objects.

## Steps

1. **count-staged-jsonl** — `tool` → `tool/object-count-report-generator`
2. **count-canonical-postgres** — `tool` → `tool/postgres-object-count-sql` (when `database_url is present`)
3. **route-missing-db-review** — `tool` → `tool/source-record-governance-router` (when `database_url is absent`)

## Defaults

- **knowledge_packs**: `knowledge-pack/object-count-db-bootstrap-patterns`

## Success criteria

- deterministic `$.object_count_report.catalog.manifest_count` > `0`
- semantic must_cover ['curated manifest count is not the same as generated object row count', 'canonical generated objects are stored in Postgres and pgvector'] against `$.object_count_report`

## Provenance

- Hub component: `pipeline/generated-object-count-reporting` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
