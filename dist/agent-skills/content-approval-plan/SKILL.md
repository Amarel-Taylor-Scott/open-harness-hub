---
name: content-approval-plan
description: Create a review-gated Postgres load plan for content approval decisions
  and derived promotion decisions.
when_to_use: 'Pipeline kind: research_web.content_approval_plan.'
---

# Content approval plan

Creates CSV, JSONL, and SQL load bundles that approve or route dedupe-resolved component candidates before active promotion.

## Task

Create a review-gated Postgres load plan for content approval decisions and derived promotion decisions.

## Steps

1. **load-content-approval-checks** — `knowledge_pack` → `knowledge-pack/content-approval-patterns`
2. **plan-content-approval** — `tool` → `tool/content-approval-planner`
3. **audit-staged-vs-committed** — `tool` → `tool/staged-vs-committed-load-auditor`

## Defaults

- **knowledge_packs**: `knowledge-pack/content-approval-patterns`

## Success criteria

- deterministic `$.content_approval_plan.content_approval_count` > `0`
- deterministic `$.content_approval_plan.promotion_decision_count` > `0`
- semantic must_cover ['content approval', 'dedupe clearance', 'promotion decisions', 'review tickets', 'quality index rows'] against `$.content_approval_plan`

## Provenance

- Hub component: `pipeline/content-approval-plan` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
