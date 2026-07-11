# Change Verification — a warrant before every change

> Portable standard for any AI Done Right project. Reference implementation:
> `docs/codex/change-verification-contract.md` + the `CLAUDE.md` "Change Verification" section.

## The rule

Every change — human-directed or from an autonomous loop — carries a **warrant** before it is
committed: evidence for *why it is correct*, not an agent's confidence. A change is admissible only
with one of three warrants:

1. **Clear user intent** — the owner explicitly asked for it. Cite it (verbatim or a tight paraphrase)
   in the commit message and the ledger. Strongest warrant; required for design / brand / strategy /
   vocabulary / pricing / irreversible changes.
2. **Corroboration** — **two or more independent agreeing sources** (research, standards, benchmarks,
   competitor evidence). One source, or one agent's assertion, is not corroboration.
3. **Established principle** — the change follows a documented repo principle. State which one.

No warrant, no commit. **"It is green" is necessary, not sufficient** — a passing change with no intent,
no corroboration, and no principle (or one that contradicts a principle) is rejected or held for the owner.

## Why

A green suite proves the code runs; it does not prove the change is *wanted* or *correct in direction*.
This project shipped a shared front end with a brand toggle on one agent's reasoning, then had it reversed
by the owner ("serious confusion between the two product surfaces"). The warrant rule makes that failure
mode structural instead of a matter of luck: design, brand, positioning, naming, product structure, and
pricing are the owner's strategic calls — an agent proposes and corroborates, it does not decide.

## Match the warrant to the blast radius

| Change class | Minimum warrant |
|---|---|
| Trivial / reversible (typo, comment, additive doc, obvious green fix) | a principle, or self-evident correctness |
| Substantive code (behavior, schema, API, data plane) | checks/tests pass **and** a principle or intent |
| **Design / brand / strategy / vocabulary / pricing / product structure** | **clear user intent OR strong corroboration — NEVER a unilateral single-agent call** |
| Irreversible / outward-facing (publish, delete, external send) | explicit intent **and** confirmation |

## How it is enforced

- **Cite the warrant in every commit and ledger line**, in one of these forms:
  `warrant: user-intent — "<quote>"` · `warrant: corroboration — <sources>` · `warrant: principle — <which>`.
- **A different agent verifies than builds.** No agent grades its own work. The verify step checks the
  *warrant* (right class, meets that class's bar, contradicts no intent or principle), not just green.
- **Supersede in place.** When a decision replaces an earlier one, update or delete the stale artifact in
  the *same* change — no orphaned contradictions.
- **Verify before relying.** A memory or doc naming a file, flag, or path is a claim about a *past* state;
  re-check it against the repo before acting on it.
- **Exceptions are allowed but recorded.** Small + reversible exceptions (emergency green-restore, an
  obvious bug fix, a flagged experiment, additive scaffolding marked `planned`) are logged with rationale
  in the session ledger. Never an exception for irreversible or design changes.

## DO / DON'T

- DO cite intent, two-plus sources, or a named principle in the commit and ledger for every change.
- DO hold design / brand / strategy / vocabulary / pricing / product-structure changes for the owner
  when you have only your own reasoning.
- DO delete the stale doc/memory in the same change that supersedes it.
- DON'T commit on "it's green" alone, or treat one agent's assertion as corroboration.
- DON'T make a unilateral single-agent call on anything in the design row.
- DON'T let one agent verify its own change.
