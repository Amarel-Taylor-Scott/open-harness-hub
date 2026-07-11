# GOAL — Perpetual, resilient, best-practices-biased improvement loop

A loop built to **keep going**: never stop early, branch on every block, always move forward to the next improvement.
The ONLY halt is `.agent/STOP_REQUESTED`. Bias hard toward shipping improvements + enforcing best practices, using the
multi-model panel (Kimi-2.7 + GLM-5.2) as both a generator of opportunities and a fallback when Claude is stuck.

## Prime directive
**Forward motion over completion.** Every cycle must leave the codebase better. There is NO "done" — when one frontier
is exhausted, move to the next. Do not stop to ask; decide from the repo, act, record. Stop ONLY on `.agent/STOP_REQUESTED`.

## No no-op cycles — resolve via best practices (owner standing authorization 2026-06-21)
**Every cycle must produce a real improvement** — never a pure health-check no-op while there is queued work. The owner
authorized the loop to **override blockers + items that "need owner judgment" by following best practices + the guiding
principles** (the best-practices charter below, the governance laws, the architecture). So:
- An item previously marked **owner_gated** for design / structure / strategy / pricing / naming is now **resolved by the
  loop via best practices**, recording the warrant (this directive + the principle applied) in the commit/ledger — no
  longer deferred. The change-verification warrant is satisfied by this clear, standing owner intent.
- The ONLY items still deferred are **irreducible-owner**: an external action, a fact only the owner has, or real
  spend/legal (`scripts/proposal_backlog.is_irreducible`) — e.g. signing a real design partner, the founder's actual
  personal credentials, moving real money, a legal/trademark filing. Even these get a **best-effort DRAFT** (a template
  + a recommended answer with rationale) + a clear flag — never a no-op.
- If a cycle finds nothing queued, **generate the next improvement** (drain the backlog, sweep for a fix, or advance a
  frontier) rather than idling. Quiet ≠ stop; quiet = find the next thing.

## Each cycle (pick the highest-leverage move; never idle)
1. **Surface opportunities** — `PYTHONPATH=. python3 scripts/multi_model_improvement_loop.py --run --limit 8`
   (sweeps the next targets across EVERY aspect — planes, wedges, architecture, business, design, presentation, demos,
   integrations, modules; ~409 targets; resilient + resumable via cursor; `--forever` re-sweeps perpetually).
2. **Triage** the new findings (`data/improvement-opportunities/findings.jsonl`): keep concrete + corroborated (both
   models, or Claude verifies vs the code); discard generic/hallucinated; verify cited symbols exist.
3. **Apply the single highest-leverage SAFE improvement** — one proof-backed increment, with a `--self-test`, keeping
   the gate suite + dependency law + family green. Lossless; archive-not-delete; never untrack; no-magic-values.
4. **Enforce best practices** (the charter below) — if a pass finds a violation, fix it (or ticket it) this cycle.
5. **Record + advance.** Append a one-line progress note; continue to the next cycle immediately.

## Branch-on-every-block (why it doesn't stop)
A block is a fork, never a stop. When something blocks, branch and keep moving:
- a fix looks risky / large → file a PROPOSAL (`scripts/proposal_backlog.py`) + pick the next safe improvement.
- a proof gate goes red → fix it or revert the increment, then continue (never leave red + never halt).
- a model lane is down / rate-limited → switch lane (cloudflare↔ollama) or continue offline on a deterministic task.
- a target errors → it's already recorded + the cursor advances; move on.
- **Claude is stuck** → defer: `python3 scripts/multi_model_improvement_loop.py --ask "<blocker>" [--context-file F]`
  → use Kimi + GLM insights/next-steps (as candidates; verify before applying), then proceed.
- the sweep finishes a full pass → re-sweep (`--forever`) or shift to applying the backlog of findings. Never idle.
- **a real LOGJAM (no clean way forward)** → don't churn: deliberate (Claude + Kimi + GLM) for DIVERGENT options and
  FORK each as a proposal/plan in the backlog (`scripts/stall_breaker.py`); if none is clearly best, the forks ARE the
  prioritized decision. Favor thin wrappers + clean abstractions so any forked path keeps maximum future flexibility.

## Comfort gate + escalation (when the loop is "uncomfortable" applying directly)
Not every finding should be auto-applied. Route every candidate through the comfort gate (`scripts/proposal_backlog.py`):
- **auto** — trivial + fully reversible (typo/docstring/dead-code/header-marked stale-doc archive) → the autofix
  flywheel applies it unattended (capped, audited, lossless).
- **propose** — riskier / larger / not clearly trivial → a SCORED, PRIORITIZED proposal in the backlog
  (`data/dev-intel/proposals-prioritized.md`). The agent reviews then applies; never auto.
- **owner_gated** — brand / pricing / portfolio-structure / strategy / naming → an owner decision (change-verification
  law: clear user intent or strong corroboration, never a unilateral single-agent call). Filed, never applied.

Escalation ladder: **act** (auto) → **propose** (scored backlog) → **deliberate** (multi-model `--ask`) →
**fork** (stall_breaker forks divergent options when there's no clean path) → **owner decision** (owner_gated). The loop
always moves DOWN this ladder rather than stopping — the worst case is a well-formed, prioritized decision, never a halt.

## Best-practices charter (bias toward these every cycle)
- **No monoliths** — split fat modules/classes into thin, focused units.
- **Thin base classes that get extended** — shared behavior in a small base, specialized via subclasses behind ports.
- **Appropriate hierarchies + taxonomy** — coherent, non-overlapping, single-sourced (no-magic-values).
- **Flexibility / no lock-in** — everything swappable behind a port (compute, LLM, search, storage backends).
- **Lossless + governed** — preserve raw + lineage; serves_truth=false for model/run output; receipts where it matters.
- **Proven** — every change lands with a `--self-test`; the gate suite stays green.

## Three tracks, handled continuously (self-improving, always)
The loop owns all three tracks at once — two cooperating loops, because a deterministic daemon cannot write feature code:
1. **Code / organization improvements** — the AGENT loop (this autonomous `/loop`): each tick triages the queued
   backlog, IMPLEMENTS the highest-leverage SAFE concrete edit (small + reversible + verifiable), runs its `--self-test`
   + the gate suite, and reverts if anything goes red. Authorized standing work (the owner asked the loop to handle this
   always) — not "inventing new work," it's draining the loop's own queue.
2. **Owner-only items** — the `yc` flywheel surfaces and keeps them prioritized (design partner, founder story,
   raise/pricing/one-liner). The loop CANNOT close these; it makes sure they're never lost or buried.
3. **Housekeeping** — the daemon's `checkpoint` flywheel auto-commits the working tree when gates are green (reversible,
   never on the default branch, never pushes), so work never piles up uncommitted.

## The single command (`./loop`) + the one objective (YC readiness)
There is ONE command. `./loop` starts the flywheel daemon if it's down/stale and prints the monitor — safe to re-run,
keeps the flywheels alive for days, restarts them if the process dies. The loop STEERS toward a single measurable
objective: **YC readiness** (`scripts/yc_readiness.py`, grounded in YC's 2026 criteria + S26 Requests-for-Startups;
full prep doc `docs/strategy/yc-readiness-and-prep-2026.md`). The `yc` flywheel scores the whole portfolio (proof,
working demo, traction, founder-market fit, who-needs-it, not-a-wrapper, competition, ask, RFS-fit) and files the open
gaps into the comfort-gated backlog so every cycle moves toward submission.
- `./loop` — start + supervise (the everyday command).  `./loop status` — read-only monitor.
- `./loop yc` — the YC-readiness scorecard + the top gaps (the marching orders).  `./loop run` — one cycle (debug).
- `./loop stop` / `./loop resume` — toggle `.agent/STOP_REQUESTED`.  `./loop logs` — tail the daemon log.

The engine is `scripts/flywheel_orchestrator.py` — TWELVE flywheels on an ADAPTIVE scheduler that runs for days
unattended (state-persisted, resilient, halts only on `.agent/STOP_REQUESTED`):
- **sweep** — one Kimi/GLM improvement+research batch -> findings; covers TOP-DOWN architecture + coordination AND
  BOTTOM-UP modules every pass (re-sweeps when a pass completes).
- **status** — writes a heartbeat to `data/dev-intel/flywheel-status.md` so you can glance at progress any time.
- **yc** — SELF-DIRECTING: scores whole-portfolio YC readiness and files the open gaps into the backlog.
- **propose** — distills findings into the SCORED, PRIORITIZED, comfort-gated proposal backlog.
- **health** — runs the core proof gates; a red gate JUMPS health to top priority until green.
- **autofix** — auto-applies ONLY trivial, fully-reversible fixes (lossless doc archive; capped + audited; `--no-autofix`).
- **cleanup** — scans for stale/superseded docs (report only; the move is owner-gated).
- **surfaces** — keeps the public sites fresh + validated: rebuilds the intro site + the 21 hub pages from the current
  registries (computed counts/catalogs auto-update) and runs their self-tests (catches drift; keeps the demo current).
- **adapters** — keeps components swappable behind agnostic wrappers: runs the drop-in test + the adapter-layers
  coverage audit (`architecture/adapter_layers.json`) and files any port GAP as a comfort-gated proposal for the agent.
- **checkpoint** — auto-commits the working tree when gates are green (track 3; reversible; never on main; never pushes).
- **logjam** — STALL-TRIGGERED: when the loop is persistently stuck (gates red across runs / a flywheel failing
  repeatedly / no new findings), it deliberates (Kimi+GLM) for DIVERGENT options and FORKS them into the backlog
  (cooldown-limited so it never churns).
Adjustments: most-overdue-by-cadence selection, health-red priority bump, error cooldown (a failing flywheel backs
off), and **stall→logjam escalation** (a red gate first retries `health`; if it stays red across enough runs it
escalates to `logjam`, which forks options rather than spinning).

## Run it (owner-launched; one loop at a time; stop via `.agent/STOP_REQUESTED`)
- **Start + monitor with `/loop` (recommended):** a self-paced `/loop` running
  `PYTHONPATH=. python3 scripts/flywheel_orchestrator.py --supervise` — each firing STARTS the flywheel daemon if it's
  down/stale and prints the MONITOR (running? cycle, health, heartbeat age, findings/research/auto-applied counts,
  per-flywheel errors). It keeps the flywheels alive for days and restarts them if the process dies. Read-only check
  anytime: `... --monitor`.
- **Unattended for days (no agent, no /loop):** `PYTHONPATH=. python3 scripts/flywheel_orchestrator.py --forever`
  — rotates all flywheels, surfaces findings + health + cleanup + a heartbeat, auto-applies trivial reversible fixes.
- **Agent-driven `/loop` (triages + APPLIES the safe fixes):** self-paced `/loop` running this doc — each firing runs a
  cycle (`flywheel_orchestrator.py --run`), then triages the new findings + applies the highest-leverage safe increment.
- Single-engine alternative: `PYTHONPATH=. python3 scripts/multi_model_improvement_loop.py --forever --limit 8`.
