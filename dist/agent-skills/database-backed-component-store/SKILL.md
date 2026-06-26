---
name: database-backed-component-store
description: Plan canonical database rows for active components and subcomponents
  from governed factory output.
when_to_use: 'Pipeline kind: research_web.database_backed_component_store.'
---

# Database-backed component store

Routes generated factory rows into a Postgres-first component and subcomponent store plan, preserving source governance, dedupe, indexing, review, and search readiness gates.

## Task

Plan canonical database rows for active components and subcomponents from governed factory output.

## Steps

1. **govern-source-rows** — `tool` → `tool/source-record-governance-router`
2. **plan-component-store** — `tool` → `tool/component-store-planner`
3. **preflight-relationships** — `tool` → `tool/factory-jsonl-relationship-preflight`
4. **route-review** — `tool` → `tool/object-factory-job-router`

## Defaults

- **knowledge_packs**: `knowledge-pack/database-component-store-patterns`

## Success criteria

- deterministic `$.component_store_plan.component_candidate_count` > `0`
- deterministic `$.component_store_plan.subcomponent_candidate_count` > `$.component_store_plan.component_candidate_count`
- semantic must_cover ['database backed components', 'subcomponents', 'source governance', 'review route', 'repository files are seed or export definitions'] against `$.component_store_plan`

## Provenance

- Hub component: `pipeline/database-backed-component-store` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
