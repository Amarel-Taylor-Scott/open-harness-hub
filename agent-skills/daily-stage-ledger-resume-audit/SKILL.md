---
name: daily-stage-ledger-resume-audit
description: Inspect one daily production run directory, prove which stages have durable
  summaries, and emit the next safe resume action.
when_to_use: 'Pipeline kind: research_web.daily_stage_ledger_resume_audit.'
---

# Daily stage ledger resume audit

Builds a resumable stage ledger for a daily component factory run so interrupted 1K to 5K candidate batches can resume from the next missing stage instead of rebuilding prior stages.

## Task

Inspect one daily production run directory, prove which stages have durable summaries, and emit the next safe resume action.

## Steps

1. **load-stage-contracts** — `knowledge_pack` → `knowledge-pack/daily-factory-stage-contracts`
2. **build-stage-ledger** — `tool` → `tool/daily-stage-ledger-builder`

## Defaults

- **knowledge_packs**: `knowledge-pack/daily-factory-stage-contracts`

## Success criteria

- deterministic `$.build-stage-ledger.stage_count` >= `5`
- semantic must_cover ['stage status', 'resume actions', 'closeout readiness', 'operator approval boundary'] against `$.build-stage-ledger`

## Provenance

- Hub component: `pipeline/daily-stage-ledger-resume-audit` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
