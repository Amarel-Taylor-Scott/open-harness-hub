---
name: staged-vs-committed-load-audit
description: Audit whether staged object-factory rows from a load plan match canonical
  Postgres row counts after load execution.
when_to_use: 'Pipeline kind: research_web.staged_vs_committed_load_audit.'
---

# Staged versus committed load audit

Compares object-factory staged bulk-load counts against canonical Postgres and pgvector row counts to prove what was actually committed after load execution.

## Task

Audit whether staged object-factory rows from a load plan match canonical Postgres row counts after load execution.

## Steps

1. **govern-load-audit-inputs** — `tool` → `tool/source-record-governance-router`
2. **run-postgres-count-report** — `tool` → `tool/postgres-object-count-sql` (when `database_url is present`)
3. **audit-staged-versus-committed** — `tool` → `tool/staged-vs-committed-load-auditor`

## Defaults

- **knowledge_packs**: `knowledge-pack/staged-vs-committed-load-audit-patterns`

## Success criteria

- deterministic `$.load_audit.preflight.ok` == `True`
- deterministic `$.mismatched_relations` == `0`
- semantic must_cover ['staged counts', 'committed Postgres counts', 'not verified when database counts are absent', 'object_count_report.sql', 'insurance scope excluded'] against `$.load_audit`

## Provenance

- Hub component: `pipeline/staged-vs-committed-load-audit` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
