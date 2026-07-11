---
name: local-smoke-command-gate
description: Gate a generated local smoke plan with command policies and emit a dry-run
  ledger before local Docker or Postgres execution.
when_to_use: 'Pipeline kind: research_web.local_smoke_command_gate.'
---

# Local smoke command gate

Applies local command policies to a generated smoke plan and produces a dry-run execution ledger plus operator approval checklist before any Docker or Postgres commands are run.

## Task

Gate a generated local smoke plan with command policies and emit a dry-run ledger before local Docker or Postgres execution.

## Steps

1. **load-local-command-policies** — `knowledge_pack` → `knowledge-pack/local-smoke-command-policies`
2. **gate-local-smoke-commands** — `tool` → `tool/local-smoke-command-gate`

## Defaults

- **knowledge_packs**: `knowledge-pack/local-smoke-command-policies`

## Success criteria

- deterministic `$.gate-local-smoke-commands.dry_run_only` == `True`
- deterministic `$.gate-local-smoke-commands.command_count` >= `1`
- semantic must_cover ['approval checklist', 'dry-run ledger', 'Docker', 'psql', 'no execution'] against `$.gate-local-smoke-commands`

## Provenance

- Hub component: `pipeline/local-smoke-command-gate` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
