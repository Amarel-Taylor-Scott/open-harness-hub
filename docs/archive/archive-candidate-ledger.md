# Archive Candidate Ledger

This ledger defines how Baltor/OpenHubForAI should identify, review, and
approve stale or rotted context without losing provenance. It is a decision
surface, not an instruction to move files.

Use it when a long-running agent or curator suspects that a document, prompt,
manifest, generated page, or operational note is no longer canonical.

## Principle

Active context should live in the right operating substrate:

- canonical specifications in `taxonomy/`, `schemas/`, and current architecture
  docs;
- active operational records in databases or generated database exports;
- published seed manifests in `catalog/`;
- historical records in `docs/archive/`;
- generated artifacts in `dist/`, `site/`, or a database-backed artifact store.

Archival is a provenance decision. A file should not be archived because it is
old, verbose, duplicated, or inconvenient. It should be archived only when the
current canonical replacement is known and references have been checked.

## Candidate States

| State | Meaning | Allowed action |
|---|---|---|
| `candidate` | The audit found freshness, duplication, or terminology risk. | Review only. Do not move. |
| `keep_active` | The file is still canonical or operationally active. | Update wording or references if needed. |
| `supersede` | The file is useful history but not the current source of truth. | Add a supersession note and canonical pointer. |
| `archive_ready` | The file can be moved after reference checks and approval. | Move only in a separate approved archival change. |
| `archived` | The file has been moved with lineage preserved. | Keep redirect notes and validate references. |

## Candidate Evidence

Every archive candidate should carry:

- path;
- current state;
- suggested action;
- severity score;
- reviewer or owning area;
- reasons;
- canonical replacement hint;
- reference-check status;
- planned archive note or redirect;
- validation command to run after any approved move.

The audit script emits these fields with:

```bash
python3 scripts/audit_context_storage.py --archive-ledger
```

## Severity Guidance

| Severity | Interpretation | Typical decision |
|---:|---|---|
| 1 | Wording, terminology, or mild freshness concern. | Keep active or revise. |
| 2 | Operational drift, unresolved TODO, or older framing. | Review against canonical docs. |
| 3 | Self-identified superseded/deprecated content. | Add supersession pointer. |
| 4+ | Multiple freshness or authority concerns. | Prepare for archival review. |

Severity is advisory. A low-severity file can still be archived if it is clearly
non-canonical, and a high-severity file can stay active if it is an operating
ledger or required prompt.

## Required Review Checks

Before any archive move:

1. Confirm the file is not an active spec, schema, required prompt, active
   operating runbook, or published manifest.
2. Identify the canonical replacement.
3. Check references from docs, catalog manifests, scripts, prompts, and the
   generated site.
4. Add a supersession note or redirect pointer.
5. Preserve enough lineage to understand why the content was archived.
6. Run validation after the move.

## Database Direction

Do not use archival as a substitute for moving active operational context into a
proper database.

Good database-backed records include:

- archive decisions;
- context freshness checks;
- source replacement pointers;
- object governance profiles;
- rubric and contract versions;
- database migration candidates;
- hard-coded setting audit findings;
- YAML seed-to-row expansion state.

Files remain useful for specifications and seed/export manifests. The operating
ledger should be database-backed once the archival workflow becomes recurring.
At that point, the audit should write append-only rows such as
`context_archive_candidate`, `context_archive_decision`, and
`context_storage_migration_candidate` instead of requiring every long-running
agent to rescan the full repository.

## Current Non-Destructive Workflow

```text
run audit
  -> inspect archive candidate ledger
  -> mark each candidate keep_active, supersede, or archive_ready
  -> update canonical replacement pointers
  -> only then perform a separate approved archive move
```

This prevents autonomous agents from deleting or moving context just because it
looks stale.
