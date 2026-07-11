---
name: source-surface-execution-summary
description: Report source-surface object-factory progress and load readiness without
  confusing generated row counts with curated YAML manifest counts.
when_to_use: 'Pipeline kind: research_web.source_surface_execution_summary.'
---

# Source surface execution summary

Aggregates source-surface factory run progress across partitions, jobs, replay records, generated rows, promotion decisions, review tickets, and load readiness.

## Task

Report source-surface object-factory progress and load readiness without confusing generated row counts with curated YAML manifest counts.

## Steps

1. **govern-summary-inputs** — `tool` → `tool/source-record-governance-router`
2. **summarize-source-surface-execution** — `tool` → `tool/source-surface-execution-summary-reporter`
3. **route-review-attention** — `tool` → `tool/object-factory-job-router`

## Defaults

- **knowledge_packs**: `knowledge-pack/source-surface-execution-summary-patterns`, `knowledge-pack/source-surface-partition-patterns`

## Success criteria

- deterministic `$.load_readiness.preflight_ok` == `True`
- deterministic `$.generated_row_total` > `0`
- semantic must_cover ['manifest count is separate from generated object rows', 'review tickets', 'promotion holds', 'bulk load readiness', 'insurance scope excluded'] against `$.execution_summary`

## Provenance

- Hub component: `pipeline/source-surface-execution-summary` v0.1.0
- License: `MIT`
- Industry: government, software, media, construction, energy, finance, healthcare, cross_industry
- Full source manifest: see `references/manifest.yaml`
