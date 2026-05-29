# Change-verification contract — warrant before change

Every update or design change carries a **warrant** before it is committed: evidence for *why it is
correct*, not an agent's confidence. This gates human-directed work **and** the autonomous loop
(`/evolve`, the workflows). It exists because this very project shipped a design change — a shared
front-end with a brand toggle — on one agent's reasoning, then had it reversed by the owner ("serious
confusion between the two product surfaces"). This contract makes that failure mode structural, not
a matter of luck.

## A change is admissible only with one of these warrants
1. **Clear user intent** — the owner explicitly asked for it. **Cite it** (verbatim or tight paraphrase)
   in the commit message + ledger. The strongest warrant; required for design/brand/strategy/vocab/
   pricing/irreversible changes.
2. **Corroboration** — **≥2 independent agreeing sources** (research, standards, benchmarks, competitor
   evidence). One source — or one agent's assertion — is *not* corroboration.
3. **Established principle** — the change follows a documented repo principle (the codex, north-stars,
   `value-propositions.md`, the capability-lift bar, `no-magic-values.md`, `schema-extensibility.md`,
   the seven-primitive grammar, the design-aesthetic). State which.

No warrant → no commit. **"It's green" is necessary, not sufficient** — a passing but unwarranted change
(no intent, no corroboration, contradicts a principle) is rejected or held for the owner.

## Proportional bar (match the warrant to the blast radius)
| Change class | Minimum warrant |
|---|---|
| Trivial / reversible — typo, comment, additive doc, obvious green fix | a principle, or self-evident correctness (exception-by-default) |
| Substantive code — behavior, schema, API, data plane | correctness verification (checks/tests pass) **and** a principle or intent |
| **Design / brand / strategy / vocabulary / pricing / product structure** | **clear user intent OR strong corroboration — NEVER a unilateral single-agent call** |
| Irreversible / outward-facing — publish, delete, external send | explicit intent **+** confirmation |

The design row is the reason this contract exists: brand, positioning, UI direction, naming, product
structure, and pricing are the **owner's strategic calls** — an agent proposes and corroborates; it does
not decide. Scope intent precisely: "CEaaS = teal **sibling**, same typography, accent swapped" is intent
for *an accent swap*; changing the whole theme **direction** is **not** covered by it and must be held.

## Exceptions (allowed — but recorded)
Exceptions are fine when proportional + reversible, and **must be logged** in
`.research-notes/autonomous-session-ledger.md` with the rationale:
- emergency green-restore (revert to a working state),
- an obvious correctness / bug fix,
- a reversible experiment behind a flag or in an isolated branch/worktree,
- additive scaffolding clearly marked `planned` / `experimental`.

"As appropriate" = **small + reversible + recorded**. Never an exception for irreversible or design changes.

## The verifier's duty (especially in the autonomous loop)
The adversarial verify step checks the **warrant**, not just green:
- Does the change cite a valid warrant (intent / ≥2 sources / principle)?
- Is it the right class, and does it meet that class's bar?
- Does it **contradict** any explicit user intent or existing principle? If so → reject.
- **No agent grades its own work** — the verifier is a different agent than the builder.

In workflows: the **prioritizer tags** each item's warrant; the **verifier confirms** it; the
**orchestrator commits** only warranted + green items and records the held/rejected ones with reasons.

## Anti-context-rot rules
- **Supersede in place.** When a decision replaces an earlier one, update or delete the stale artifact
  in the *same* change — no orphaned contradictions (the dead shared-front-end approach's doc/memory
  references must go with it).
- **Verify before relying.** A memory or doc that names a file, flag, or path is a *claim about a past
  state* — re-check it against the repo before acting on it.
- **One source of truth.** Reconcile conflicting docs; don't stack them. Counts are computed, never
  typed (`no-magic-values.md`). A decision and its rationale live together.
- **Reconcile as you go.** The loop fixes drift it notices (stale refs, contradictions) as part of the
  work, not "later."

## How to apply
Cite the warrant in each commit + ledger line:
`warrant: user-intent — "<quote>"` · `warrant: corroboration — <sources>` · `warrant: principle — <which>`.
Referenced by `CLAUDE.md` and the goal commands (`/evolve`, `/goal`, `/launch`). Related:
`docs/codex/no-magic-values.md`, `docs/codex/schema-extensibility.md`, the capability-lift bar.
