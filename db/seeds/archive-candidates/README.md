# Context Archive Candidate Seed Package

This directory contains database-ready seed rows for the
`context_archive_candidate` table in `db/postgres/schema.sql`.

The package follows the repository storage direction:

```text
Markdown and prompts remain reviewable source artifacts.
Archive decisions are tracked as database rows before any file move happens.
```

## Files

```text
context_archive_candidate.jsonl
load-context-archive-candidates.sql
```

`context_archive_candidate.jsonl` is generated from the non-destructive context
storage audit. Each row records the path, severity, reasons, inferred
replacement, required curator checks, source hash, and suggested action.

The generated SQL is a reviewable psql load example:

```bash
psql "$DATABASE_URL" -f db/seeds/archive-candidates/load-context-archive-candidates.sql
```

## Rules

- A candidate row does not approve moving, deleting, or rewriting a file.
- Curators must check inbound references before any archive move.
- Canonical specs, active prompts, and operating runbooks must be explicitly
  marked `keep_active` or superseded with a replacement pointer.
- Source hashes are recorded so archive review can detect drift between audit
  time and curator action.
