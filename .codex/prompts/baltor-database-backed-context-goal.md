# /goal: Database-Backed Baltor Context And Anti-Rot Migration

You are an autonomous Codex agent working in this repository. Improve the
Baltor/Open Harness Hub context-object system for a long-running session. Do
not stop at proposals. Implement, validate, record, and continue until the
human interrupts you or a real safety/destructive-action blocker prevents
progress.

The active tool goal in this thread may already be occupied by another
long-running objective. This file is the repo-level durable goal prompt for the
database-backed context migration work.

## Mission

Move Baltor from file-heavy catalog thinking toward database-backed operational
context while preserving YAML/Markdown as seed, export, review, and portability
artifacts.

Primary goals:

```text
1. Strengthen guidelines for database-backed context objects.
2. Identify stale, duplicated, or rotted context.
3. Archive rotted context deliberately with aliases and references preserved.
4. Move YAML-only concepts toward database rows and import/export flows.
5. Move hard-coded settings into registries, vocabularies, schemas, config, or database tables.
6. Treat business/database objects as governed objects with rubrics, contracts,
   schemas, layouts, diagrams, and required context rules.
7. Validate every change.
```

## Read First

1. `AGENTS.md`
2. `README.md`
3. `taxonomy/SPEC.md`
4. `docs/codex/no-magic-values.md`
5. `docs/architecture/database-backed-context-catalog.md`
6. `docs/architecture/baltor-business-object-governance-standard.md`
7. `docs/architecture/baltor-rubric-research-and-hierarchical-standard.md`
8. `docs/architecture/baltor-executive-rubric-suite.md`
9. `db/postgres/schema.sql`
10. `db/README.md`

## Operating Loop

```text
ORIENT
  Read current docs, schema, validation state, and latest audit output.

AUDIT
  Run scripts/audit_context_storage.py and inspect YAML, hard-coded settings,
  stale docs, and database-migration candidates.

DESIGN
  Pick one narrow migration target: a setting registry, a database table, a
  manifest-to-row expansion, an archive policy, or a validation rule.

BUILD
  Implement the smallest durable improvement that reduces file rot or hard-coded
  drift.

VALIDATE
  Run targeted validation and py_compile for changed scripts. Run full
  scripts/validate.py when catalog manifests change.

RECORD
  Update docs or ledger with what changed, what remains, and which files are
  migration candidates.

REPEAT
  Continue without asking unless a destructive archive/move or external install
  requires approval.
```

## Hard Rules

- Do not delete or move existing files without an archive map and human approval
  unless the user explicitly asks for the move.
- Do not break public catalog seed/export behavior.
- Do not make the database the only way to read public static documentation.
- Do not store PII, secrets, credentials, or private customer data in examples.
- Do not add another hard-coded list when a schema, vocabulary, database table,
  or config registry can own it.
- Do not silently rename published component IDs.
- Do not use the acronym `PMF` in new prose; write `product-market fit`.

## What To Build

Prioritize:

```text
database-backed rubric dimensions and scores
database-backed object governance packages
component-to-context-object bindings
mask and transformer contracts
manifest import/export tooling
hard-coded settings registry
archive policy and stale-context audit
validation checks for drift
SQL views for operational dashboards
docs that explain files-as-seeds and database-as-operational-truth
```

## Archive Policy

Archive only when:

```text
the content is superseded by a newer canonical doc;
references have been checked;
an alias or redirect note exists;
the archive reason is recorded;
the archive location is documented;
validation still passes.
```

Preferred archive locations:

```text
docs/archive/
catalog/_inbox/archive-candidates/
```

## Closeout

A closeout must include:

```text
files changed
audit findings
database-backed migration progress
rotted-context candidates found
archive actions taken or deferred
hard-coded settings removed or queued
validation commands run
next recommended migration target
```

