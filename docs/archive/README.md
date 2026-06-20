# Archive

This directory holds intentionally archived documentation and context artifacts.
It is not a trash directory.

Use this archive when content is superseded, stale, duplicated, or no longer
canonical but still needs to be preserved for provenance.

## Rules

Before moving content here:

```text
1. Confirm the content is superseded, stale, duplicated, or non-canonical.
2. Identify the current canonical replacement.
3. Check references from docs, catalog manifests, scripts, and prompts.
4. Add an archive note or redirect pointer.
5. Preserve enough context for lineage.
6. Run validation after the move.
```

Use [`archive-candidate-ledger.md`](archive-candidate-ledger.md) before moving
anything. The ledger treats archive review as a context-governance decision:
candidates can be marked `candidate`, `keep_active`, `supersede`, or
`archive_ready` before any approved file move happens.

Generate a non-destructive candidate ledger with:

```bash
python3 scripts/audit_context_storage.py --archive-ledger
```

Do not archive:

```text
active specs
canonical schemas
current product docs
published component manifests
files still referenced by required prompts
```

Prefer database-backed operational records for active context. Files in this
directory are historical records and review artifacts.
