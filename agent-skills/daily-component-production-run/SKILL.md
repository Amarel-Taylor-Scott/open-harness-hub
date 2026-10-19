---
name: daily-component-production-run
description: Run one repeatable daily production pass that expands database-backed
  component candidates and product-ready showcase pipeline templates.
when_to_use: 'Pipeline kind: research_web.daily_component_production_run.'
---

# Daily component production run

Executes the daily factory path for 1,000 to 5,000 component candidates, 5 to 25 showcase pipelines, coverage scoring, gap backfill, and staged load audit.

## Task

Run one repeatable daily production pass that expands database-backed component candidates and product-ready showcase pipeline templates.

## Steps

1. **load-production-run-checks** — `knowledge_pack` → `knowledge-pack/daily-production-run-patterns`
2. **run-daily-production** — `tool` → `tool/daily-production-runner`
3. **daily-closeout-review** — `tool` → `tool/daily-partition-load-auditor`

## Defaults

- **knowledge_packs**: `knowledge-pack/daily-production-run-patterns`, `knowledge-pack/daily-showcase-pipeline-patterns`, `knowledge-pack/showcase-candidate-coverage-patterns`, `knowledge-pack/showcase-gap-component-patterns`

## Success criteria

- deterministic `$.run-daily-production.generated.component_candidates` >= `1000`
- deterministic `$.run-daily-production.generated.showcase_templates` >= `5`
- deterministic `$.run-daily-production.load_audit.audit_status` == `staged_only`
- semantic must_cover ['component candidates', 'showcase pipelines', 'coverage', 'gap fill', 'load audit', 'review gate'] against `$.run-daily-production`

## Provenance

- Hub component: `pipeline/daily-component-production-run` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
