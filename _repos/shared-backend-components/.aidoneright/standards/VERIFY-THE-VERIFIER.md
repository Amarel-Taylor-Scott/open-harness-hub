# Verify the Verifier — a green suite that can never go red proves nothing

> Portable standard for any AI Done Right project. Reference implementation (the quality ratchet):
> `scripts/check_quality_ratchet.py`. Related gates: the determinism checks
> (`scripts/check_determinism_*.py`, "two reads are byte-identical") and the pycache/seed traps below.

## The rule

A passing test suite is worthless if it *cannot fail* on a real defect. Every verifier must itself be
verified to have teeth, via three gates:

1. **Mutation gate.** Inject a real defect into the code the gate protects and confirm the gate goes
   **red**. A gate that stays green under a genuine mutation is toothless and must be strengthened or
   removed. Each verifier ships a pure/offline `--self-test` that proves regression is caught (a
   deliberately-wrong input makes it fail) — see the reference ratchet's `self_test()`.
2. **Determinism gate.** Build the artifact **twice** and require the outputs to be **byte-identical**
   (same ids, same ordering) across two runs, even with a different clock. A non-deterministic build hides
   drift and makes every downstream diff a false signal.
3. **Quality ratchet.** Record each headline metric as a **floor computed from a manifest** (never
   hand-typed). A later run **below** the floor is a hard failure; a better run **ratchets the floor up**.
   This closes the "demo prints numbers and passes regardless while a real capability quietly rots" failure
   mode. `scripts/check_quality_ratchet.py` is the reference: floors live in a computed floors file, a
   regression below a floor fails, an improvement ratchets up, and an **unsupplied external metric emits a
   gap record — never a fabricated pass**.

## Why

The core lie a test suite can tell is "everything is fine" when nothing is actually being checked. Numbers
that only ever go up but can never trip, builds that differ run to run, and demos that pass unconditionally
all produce false green. These gates make the *verifier's own failure* observable.

## Two traps that silently defeat a harness (avoid both)

- **Never seed a reproducible harness with `hash()`.** Python's built-in `hash()` is salted per process
  (`PYTHONHASHSEED`), so a "reproducible" run keyed on it is different every process and its determinism
  gate is meaningless. Use a **stable string seed** (or a canonical content hash), not `hash()`.
- **Any edit-then-restore harness must run `PYTHONDONTWRITEBYTECODE=1` and purge `__pycache__`.** A
  mutation harness that edits a file, runs, then restores it can read a stale compiled `.pyc` from cache
  and see the *pre-mutation* behavior — a false green for the mutation gate. Disable bytecode writing and
  clear `__pycache__` around every mutate/restore cycle.

## How it is enforced

- Every verifier carries a `--self-test` that is pure and offline and demonstrates it catches a real
  defect; the self-test is wired into the proof runner so a toothless gate is itself caught.
- Determinism checks assert byte-identical repeated builds.
- The quality ratchet reads floors from computed manifests, fails on a silent regression, and records a
  gap (not a pass) for any metric a real run did not supply.

## DO / DON'T

- DO ship every gate with a `--self-test` that proves an injected defect turns it red.
- DO build twice and assert byte-identical output for anything that claims determinism.
- DO drive floors from computed manifests and fail on any drop below them.
- DO use a stable string seed; set `PYTHONDONTWRITEBYTECODE=1` and purge `__pycache__` in edit/restore harnesses.
- DON'T trust a green suite you have never watched go red.
- DON'T seed a reproducible harness with `hash()`.
- DON'T fabricate a pass for a metric no real run supplied — record a gap.
