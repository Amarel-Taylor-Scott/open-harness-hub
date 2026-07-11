---
name: dedupe-resolution-plan
description: Create a review-gated Postgres load plan for dedupe resolutions, quality
  index rows, review tickets, and candidate dedupe review updates.
when_to_use: 'Pipeline kind: research_web.dedupe_resolution_plan.'
---

# Dedupe resolution plan

Creates CSV, JSONL, and SQL load bundles that resolve dedupe clusters separately from content approval and active component promotion.

## Task

Create a review-gated Postgres load plan for dedupe resolutions, quality index rows, review tickets, and candidate dedupe review updates.

## Steps

1. **load-dedupe-resolution-checks** — `knowledge_pack` → `knowledge-pack/dedupe-resolution-patterns`
2. **plan-dedupe-resolution** — `tool` → `tool/dedupe-resolution-planner`
3. **audit-staged-vs-committed** — `tool` → `tool/staged-vs-committed-load-auditor`

## Defaults

- **knowledge_packs**: `knowledge-pack/dedupe-resolution-patterns`

## Success criteria

- deterministic `$.dedupe_resolution_plan.dedupe_resolution_count` > `0`
- deterministic `$.dedupe_resolution_plan.candidate_dedupe_update_count` > `0`
- semantic must_cover ['dedupe resolution', 'content approval remains separate', 'quality index records', 'review tickets', 'candidate updates'] against `$.dedupe_resolution_plan`

## Provenance

- Hub component: `pipeline/dedupe-resolution-plan` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
