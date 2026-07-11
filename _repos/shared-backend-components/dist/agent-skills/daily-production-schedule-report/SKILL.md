---
name: daily-production-schedule-report
description: Compare daily component production runs and recommend whether the next
  run should scale, hold, rotate matrix, or prioritize gap fill.
when_to_use: 'Pipeline kind: research_web.daily_production_schedule_report.'
---

# Daily production schedule report

Builds a trend report over daily production runs and emits the next recommended component factory command.

## Task

Compare daily component production runs and recommend whether the next run should scale, hold, rotate matrix, or prioritize gap fill.

## Steps

1. **load-scheduler-checks** — `knowledge_pack` → `knowledge-pack/daily-production-scheduler-patterns`
2. **build-schedule-report** — `tool` → `tool/daily-production-scheduler`

## Defaults

- **knowledge_packs**: `knowledge-pack/daily-production-scheduler-patterns`, `knowledge-pack/daily-production-run-patterns`

## Success criteria

- deterministic `$.build-schedule-report.run_count` >= `1`
- semantic must_cover ['target count', 'matrix', 'showcase count', 'gap fill', 'reason'] against `$.build-schedule-report.next_run_recommendation`
- semantic must_cover ['coverage rate', 'duplicate rate', 'component candidates', 'review tickets', 'staged rows'] against `$.build-schedule-report`

## Provenance

- Hub component: `pipeline/daily-production-schedule-report` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
