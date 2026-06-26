---
name: approved-promotion-smoke-test
description: Prove that an approved component candidate can flow through active component
  publication, component versioning, CDC rows, index projection, and review routing.
when_to_use: 'Pipeline kind: research_web.approved_promotion_smoke_test.'
---

# Approved promotion smoke test

Runs a synthetic approved candidate through active component promotion, component versioning, CDC, index projection, and review-ticket routing.

## Task

Prove that an approved component candidate can flow through active component publication, component versioning, CDC rows, index projection, and review routing.

## Steps

1. **load-smoke-checks** — `knowledge_pack` → `knowledge-pack/approved-promotion-smoke-patterns`
2. **run-approved-promotion-smoke** — `tool` → `tool/approved-promotion-smoke-planner`

## Defaults

- **knowledge_packs**: `knowledge-pack/approved-promotion-smoke-patterns`

## Success criteria

- deterministic `$.approved_promotion_smoke_plan.ok` == `True`
- semantic must_cover ['approved component', 'component version', 'component change event', 'index record', 'review ticket'] against `$.approved_promotion_smoke_plan`

## Provenance

- Hub component: `pipeline/approved-promotion-smoke-test` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
