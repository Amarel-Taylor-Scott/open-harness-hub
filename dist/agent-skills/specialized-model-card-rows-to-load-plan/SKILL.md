---
name: specialized-model-card-rows-to-load-plan
description: Create a review-gated Postgres/pgvector load plan from specialized model-card
  row families.
when_to_use: 'Pipeline kind: research_web.specialized_model_card_load_plan.'
---

# Specialized model-card rows to load plan

Preflights specialized model-card row families, scores promotion readiness, emits review tickets and quality index rows, and exports a Postgres/pgvector bulk-load package.

## Task

Create a review-gated Postgres/pgvector load plan from specialized model-card row families.

## Steps

1. **govern-load-plan-inputs** — `tool` → `tool/source-record-governance-router`
2. **emit-load-plan** — `tool` → `tool/specialized-model-card-load-plan-emitter`
3. **route-load-review** — `tool` → `tool/object-factory-job-router`

## Defaults

- **knowledge_packs**: `knowledge-pack/specialized-model-card-row-patterns`, `knowledge-pack/specialized-model-card-load-plan-patterns`

## Success criteria

- deterministic `$.preflight_report.ok` == `True`
- deterministic `$.promotion_summary.promotion_decisions` > `0`
- semantic must_cover ['load_sql', 'csv_paths', 'source_record', 'normalized_object', 'promotion_decision', 'index_record'] against `$.bulk_manifest`

## Provenance

- Hub component: `pipeline/specialized-model-card-rows-to-load-plan` v0.1.0
- License: `MIT`
- Industry: healthcare, finance, legal, software.devops, media, security, privacy, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
