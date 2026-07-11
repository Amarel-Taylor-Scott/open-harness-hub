# /goal: Baltor Perpetual Parallel Improvement

Work autonomously in this repo. Improve Baltor/OpenHubForAI continuously
until the human interrupts, a workspace/tool limit stops the run, or a real
safety/destructive-action blocker prevents progress. Do not stop at proposals.
Implement, validate, record, integrate parallel-agent outputs, and repeat.

Read first:

```text
AGENTS.md
README.md
taxonomy/SPEC.md
docs/codex/no-magic-values.md
_repos/baltor/context/codex/baltor-database-backed-context-current-state.md
_repos/baltor/context/codex/baltor-perpetual-parallel-improvement-runbook.md
docs/architecture/database-backed-context-catalog.md
_repos/baltor/context/architecture/baltor-business-object-governance-standard.md
db/postgres/schema.sql
```

Direction:

```text
YAML/Markdown = seed, export, review, static-doc artifacts.
Database rows = operational truth for hosted/runtime systems.

Every important object type needs rubrics, contracts, schemas, layouts,
diagrams, required context rules, relationships, dimensions, lifecycle, events,
storage mapping, policy, and audit trail.
```

Parallel workstreams:

```text
A database-backed catalog import/export
B object governance seed packages
C rotted-context archive readiness
D hard-coded settings removal
E admin demo/runtime visibility
F validation and drift gates
```

Loop:

```text
ORIENT   Read current state, git status, and recent agent outputs.
SPAWN    Start sidecar agents for disjoint write scopes when useful.
BUILD    Work locally on the critical path while agents run.
VALIDATE Run targeted checks; full validate when catalog/schema changes.
RECORD   Update state docs, ledgers, or runbooks.
INTEGRATE Review agent outputs and preserve non-conflicting changes.
REPEAT   Continue to next highest-value gap.
```

Safety:

```text
Do not terminate processes unless explicitly asked.
Do not delete/move files without explicit approval.
Do not rename published component IDs silently.
Do not revert user or other-agent changes.
Do not store secrets, credentials, PII, or private customer data.
Do not use PMF acronym in new prose; write product-market fit.
Do not remove static export/review paths when adding database storage.
```

Closeout only when forced. Include agents/statuses, files changed, database
migration progress, archive/rot findings, settings removed or queued,
validation run, still-running commands/agents, and next threads to resume.

