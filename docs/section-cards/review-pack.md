# Review Pack — section card

Section: `review_pack` (category: governance) · critical-path.

## Purpose

Trust must be independently re-runnable, not asserted. The review pack generates a timestamped,
independently-verifiable checklist: it runs the SAME verification battery a skeptical reviewer would run by
hand, derives a PASS/FAIL + a one-line evidence string per check, and writes a report so the reviewer can
re-run every command themselves. This is the governance artifact that lets someone outside the build confirm
the product works.

## Owner module

`scripts/make_review_pack.py` — `build_report(...)`, `run_check(...)`; writes
`e2e/artifacts/review-pack/REVIEW-<UTC>.md` plus a stable `REVIEW-latest.md`. Surfaced at the `/reviews` UI
page.

## Contracts

Output: `review_pack` (a checklist report: per-check command + PASS/FAIL + evidence line).

## Proof scripts

`scripts/make_review_pack.py` (own `--self-test`) and `scripts/check_review_pack_recorders.py` (guards that
every listed review-pack screenshot has a real producer) — both registered in the flywheel.

## Commands

```bash
PYTHONPATH=. python3 scripts/make_review_pack.py --self-test
PYTHONPATH=. python3 scripts/check_review_pack_recorders.py --self-test
```

## Limitations

The screenshot/visual evidence list is hand-maintained against the e2e recorders; the recorder guard catches
drift but the curated list itself is manual. The report timestamp is injected, not wall-clock, for
determinism.

## Opportunities

Auto-derive the screenshot list from the recorder registry so the curated list cannot drift from its
producers.
