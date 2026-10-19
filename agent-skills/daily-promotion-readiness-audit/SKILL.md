---
name: daily-promotion-readiness-audit
description: Determine which staged daily component candidates are ready for candidate-table
  load and which remain blocked from active promotion.
when_to_use: 'Pipeline kind: research_web.daily_promotion_readiness_audit.'
---

# Daily promotion readiness audit

Audits a staged daily production run and routes rows by candidate-load readiness, review blockers, embedding execution blockers, and active promotion readiness.

## Task

Determine which staged daily component candidates are ready for candidate-table load and which remain blocked from active promotion.

## Steps

1. **load-readiness-checks** — `knowledge_pack` → `knowledge-pack/daily-promotion-readiness-patterns`
2. **plan-promotion-readiness** — `tool` → `tool/daily-promotion-readiness-planner`

## Defaults

- **knowledge_packs**: `knowledge-pack/daily-promotion-readiness-patterns`, `knowledge-pack/daily-production-run-patterns`

## Success criteria

- deterministic `$.plan-promotion-readiness.counts.candidate_load_ready` >= `1`
- deterministic `$.plan-promotion-readiness.counts.structural_blocked` == `0`
- semantic must_cover ['candidate load', 'active promotion', 'review tickets', 'embedding execution', 'no Postgres side effects'] against `$.plan-promotion-readiness`

## Provenance

- Hub component: `pipeline/daily-promotion-readiness-audit` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
