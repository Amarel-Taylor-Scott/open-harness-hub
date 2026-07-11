# Archival — move, never delete; never untrack

> Portable standard for any AI Done Right project. Reference implementation: the `CLAUDE.md`
> "Archived / Legacy Files" section, the mover `scripts/archive_legacy_docs.py`, the status index
> `archive/legacy/README.md`, and the record file `archive/legacy/_manifest.jsonl`.

## The rule

Outdated or superseded context is **moved, not deleted, and not untracked**. It stays in git for lineage
and rollback, relocated under **`archive/legacy/<original-path>`**, with its status recorded. This is the
lossless-distillation law applied to documents: **superseded ≠ deleted**.

- **Move with the tool, not by hand.** `scripts/archive_legacy_docs.py` (`--scan` to list, `--apply` to
  move losslessly). Detection is conservative — header markers only (superseded-by / deprecated /
  do-not-use) — so a live doc is never archived by accident.
- **A status label is mandatory.** Every move is recorded in `archive/legacy/_manifest.jsonl`
  (original_path, reason, status, reversible) and surfaced in `archive/legacy/README.md` (the human status
  index plus restore instructions).
- **Archived files leave the model context but stay on disk.** The codemap / context builder excludes
  `archive/` (a tree-exclude), so archived files drop out of the model context automatically — but remain
  tracked in git.
- **Restore is a git move.** `git mv archive/legacy/<path> <path>`; the manifest holds the exact origin.
- **Status-accuracy law.** Never mislabel live or generated data as "legacy." Generated output and the live
  registry are marked as such (a `_STATUS.md`) and are never archived as outdated.

## Why

Deleting a superseded doc destroys the lineage that lets you see *why* a decision changed and roll back if
it was wrong. Leaving it in the live tree is the opposite failure: it keeps misleading humans and agents.
Moving it under `archive/legacy/` with a recorded status resolves both — the history survives for audit and
rollback, while the live context stays honest and the model stops reading dead guidance.

## How it is enforced

- The mover writes an append-only manifest record and updates the status README on every move, so an
  archived item without a status is visible as a gap.
- The context/codemap builder's tree-exclude keeps `archive/` out of model context automatically.
- Conservative header-marker detection prevents archiving a doc that has not declared itself superseded.

## DO / DON'T

- DO move superseded docs to `archive/legacy/<original-path>` with the mover, keeping them tracked in git.
- DO record original_path, reason, status, and reversibility in the manifest and status README.
- DO restore with `git mv` from the path the manifest records.
- DON'T `rm` or untrack an outdated doc — you destroy its lineage and rollback target.
- DON'T leave a superseded doc in the live tree to keep misleading readers.
- DON'T label live or generated data as "legacy," and don't archive it.
