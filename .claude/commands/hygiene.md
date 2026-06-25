# /hygiene — sweep the repo for rot and keep context honest

Run the standing hygiene contracts, report what's rotten, and clean the safe wins **losslessly** (move-not-delete).
This is the manual companion to the edit-time `scripts/hooks/hygiene_guard.py` hook and the gate's `check_*` contracts.

## 1. Detect (run these, summarize the counts — don't dump raw output)

```bash
PYTHONPATH=. python3 scripts/check_context_freshness.py --check   # broken refs + un-archived superseded
PYTHONPATH=. python3 scripts/check_northstar_design.py --check    # placeholders / side designs / kit-consistency
PYTHONPATH=. python3 scripts/audit_magic_numbers.py               # magic-number candidates (worst files first)
PYTHONPATH=. python3 scripts/archive_legacy_docs.py --scan        # docs marked superseded/deprecated
```

## 2. Clean (only SAFE, owner-aligned wins — never break a reference)

- **Broken references** (`check_context_freshness`): fix the link if the target moved; if the target is gone for good,
  remove the dead reference. Do NOT invent a file to satisfy a ref.
- **Superseded docs** (`archive_legacy_docs --scan`): move to `archive/legacy/<path>` with
  `python3 scripts/archive_legacy_docs.py --apply` (records the manifest + README). Verify nothing live links to it first.
- **Magic numbers**: in the worst file, give each load-bearing literal a named constant + a unit/rationale comment, or
  add a truly-neutral value to that audit's `_ALLOWED`. One file per sweep — don't bulk-edit blindly.
- **Placeholders / side designs** (`check_northstar_design`): real content or remove; collapse side designs into the one
  northstar surface.

## 3. Verify + record

- Re-run the four checks; the counts must not regress.
- `PYTHONPATH=. python3 scripts/run_proofs.py` stays green.
- Commit on a branch with a warrant (cite owner intent: "keep context up to date"). Update `docs/NORTHSTAR.md` if a
  canonical pointer changed. Never delete — archive. Carry the LOSSLESS DISTILLATION CLAUSE.

## Rules
- **Lossless:** archived ≠ deleted; every move recorded in `archive/legacy/_manifest.jsonl`.
- **No new rot:** don't add a reference to a file that doesn't exist; don't add a bare magic number.
- **Canonical first:** `CLAUDE.md`, `AGENTS.md`, `docs/NORTHSTAR.md` must have zero broken refs (the gate enforces this).
