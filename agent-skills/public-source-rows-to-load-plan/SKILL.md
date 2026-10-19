---
name: public-source-rows-to-load-plan
description: Create a safe additive load plan for public-source generated objects
  after replay row emission.
when_to_use: 'Pipeline kind: research_web.public_source_load_plan.'
---

# Public source rows to load plan

Turns public-source replay row families into a relationship-preflighted, promotion-scored, review-routed, bulk-load-ready Postgres and pgvector load plan.

## Task

Create a safe additive load plan for public-source generated objects after replay row emission.

## Steps

1. **govern-public-source-load** — `tool` → `tool/source-record-governance-router`
2. **emit-load-plan** — `tool` → `tool/public-source-load-plan-emitter`
3. **bulk-copy-contract** — `tool` → `tool/factory-jsonl-bulk-copy-loader`
4. **route-review-holds** — `tool` → `tool/candidate-primitive-promotion-scorer`

## Defaults

- **knowledge_packs**: `knowledge-pack/public-source-load-plan-patterns`, `knowledge-pack/public-source-replay-row-patterns`

## Success criteria

- deterministic `$.preflight_report.ok` == `True`
- deterministic `$.bulk_manifest.ok` == `True`
- semantic must_cover ['promotion decisions', 'review tickets', 'index records', 'hold before promotion'] against `$.promotion_summary`

## Provenance

- Hub component: `pipeline/public-source-rows-to-load-plan` v0.1.0
- License: `MIT`
- Industry: government, software, media, construction, energy, finance, healthcare, cross_industry
- Full source manifest: see `references/manifest.yaml`
