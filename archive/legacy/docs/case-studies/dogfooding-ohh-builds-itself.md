# Case study — the platform builds itself

> **What this is.** Open Harness Hub's thesis is that a base model gets reliable when you wrap it in a
> *bounded* harness, *governed* knowledge, and a *measured* gate. This case study is the proof we live
> on our own dogfood: **the same machinery we sell — the foundry, the `/goal` and `/evolve` loops, the
> multi-agent build workflows, the measurement engine, and this repository's change-verification
> contract — is what develops Open Harness Hub itself.** The product is its own first customer.
>
> **Honesty note, up front.** This is a case study, not a launch metric. It distinguishes what is
> *automated*, what is *human-gated*, and what is still *spec*. Where a number isn't computed, it says
> so. No invented metrics, no aspirational counts dressed as shipped.

**Warrant.** *User intent* — the owner asked for "acquihire prep + full docs + dogfood + use
cases/case studies/inspiration"; this is the dogfooding case study. *Established principle* — every
claim below is checked against the live repo per the change-verification contract
([[../codex/change-verification-contract.md]]), and the build loop it describes is the one the
`/goal`, `/evolve`, and `/direction` commands actually run against [[../codex/master-goal.md]] and
[[../codex/foundry-build-loop.md]].

---

## The argument in one line

We claim the wrapper — bounded harness + governed corpus + measured gate — turns an unreliable base
model into a dependable system. **Developing this codebase is itself an unreliable-LLM problem** (an
agent confidently ships the wrong thing). So we solved it the product way: we wrapped the development
agent in the same three things. If the thesis works anywhere, it has to work on us first.

```
  THE PRODUCT (what we sell)                  DOGFOODING (how we build it)
  ─────────────────────────────              ──────────────────────────────
  bounded harness  ───────────────────────▶  the /goal · /evolve loop + the
   (a DAG with I/O gates)                      multi-agent build workflow
  governed corpus  ───────────────────────▶  the repo's docs/codex + ledger
   (provenance, CDC, signed)                   as the agent's grounded memory
  measured gate    ───────────────────────▶  the foundry's evidence gate +
   (lift over a bare model)                    the change-verification contract
```

The rest of this document walks the three columns left-to-right.

---

## 1. The foundry mints components — and it minted itself green

The foundry (`scripts/foundry/`) is the evidence-driven generation engine we ship: a candidate
component is admitted **only** with all three pillars — a **measured gap** (the bare model
demonstrably fails), a **real licensed source** (`source_url` + author + license), and a **measured
lift** (`pipeline_score − bare_model_score > 0`). The anti-filler guarantee is not a policy applied
after the fact; it is structural, encoded in one place — `Candidate.evidence_status()` in
`scripts/foundry/contracts.py` — which the gate enforces and which a cross-product clone can never
satisfy. Design: [[../architecture/evidence-driven-component-factory.md]]; runnable loop:
[[../codex/foundry-build-loop.md]].

**The dogfood move:** the foundry is *itself* a set of components in our own taxonomy — eight modular
stages threaded by an orchestrator (`pipeline.py`), each a `Stage.run(batch, ctx) -> batch` transform
that annotates candidates and drops the unworthy *with a recorded reason*. We did not build it and
hope. We built it to **prove itself on every run**: each module ships its own `--self-test`, and the
end-to-end proof is one command:

```bash
python -m scripts.foundry.pipeline --self-test     # gap → … → gate → promoted, offline, no cost
```

That self-test is green in this repository today (verified by running it for this write-up, not
asserted). On the built-in ESG/CSDDD fixture it threads four seed gaps through the funnel and promotes
exactly two — a **Knowledge Corpus** and a **Conditional** built from one regulation source — while
dropping a weak gap at discovery, a same-source clone at novelty, and a *no-lift* candidate at the
gate. The funnel it prints is the same shape the daily contract reports:

```
areas_probed=4 → gaps_confirmed=3 → sources_found=3 → drafts_built=5
              → standardized=5 → novel=3 → lift_measured=3 → promoted=2
```

The lesson the fixture teaches on purpose: **`promoted ≠ generated`.** Five drafts were built; two
cleared the bar. A run that "generates 10,000" and promotes two scored *two*. That is the metric the
whole platform — and this dogfooding loop — reports.

---

## 2. The `/goal` and `/evolve` loops *are* harness orchestration

Open Harness Hub sells *bounded* pipelines: a DAG with input/output rules, a lift gate, and a trace.
The development loop is the same object, one level up. `/evolve` (`.claude/commands/evolve.md`) is the
umbrella harness — it subsumes `/goal` (the factory), `/launch` (both product surfaces + tunnels), and
`/polish` (the app), choosing among them by **where the platform is weakest right now**. Each cycle is
a bounded transform with explicit pre- and post-conditions:

```
ORIENT   read the ledger + services/registry.yaml + git log → name the weakest surface
PLAN     state the ONE defensible improvement this cycle produces
BUILD    the durable change (real implementation, no shortcut)
VALIDATE the gates below — "green" is a precondition for RECORD, not the goal
RECORD   append ONE ledger line (the durable cross-run memory)
BRANCH   blocked? switch lanes, note the roadblock + fallback — never stop
REPEAT
```

This is harness orchestration applied to ourselves, and it honors the same hard rules the product
enforces:

- **Bounded inputs.** The loop reads a fixed, governed context first — `docs/codex/master-goal.md`
  (the single canonical goal), the architecture docs, `services/registry.yaml` (the live `active` vs
  `planned` map), and `.research-notes/autonomous-session-ledger.md` (what the last run did). It does
  not free-associate from training data; it grounds in the repo, exactly as a Baltor-served agent
  grounds in a governed corpus.
- **Bounded outputs.** "Stage only YOUR files — the working tree carries pre-existing drift; never
  `git add -A`." This is the I/O gate of the development harness: a deliberate output boundary so one
  agent's commit can't smear another's working state.
- **A branch-on-block contract.** `/direction` (`.codex/prompts/direction.md`) is the no-stop rule:
  "task done" → next menu item; "blocked / red" → roll back to green, switch paths, keep going. Safety
  gates (no PII, no `_reference` republish, no faked embeddings, promotion boundary) are honored *by
  doing the safe thing and continuing* — they are never stop conditions. That is precisely how a
  production harness treats a failing I/O check: route, don't crash.

The factory loop has a more specialized form for component generation —
[[../codex/foundry-build-loop.md]]'s **priority ladder** (keep the self-test green → wire the real
seams → run real partitions → widen veins). The ladder is itself a Conditional: *do the highest
**unblocked** item*; if a seam is blocked (no model route, no embedder, a rate-limited source), fall
through to the next. The development agent is running a rule-pack on its own work queue.

---

## 3. The multi-agent workflow — separation of duties, on ourselves

The product separates **build** from **verify** (no harness grades its own output). The development
workflow does the same with *different agents for different duties*, because "no agent grades its own
work" is the load-bearing rule of the change-verification contract:

> In workflows: the **prioritizer tags** each item's warrant; the **verifier confirms** it; the
> **orchestrator commits** only warranted + green items and records the held/rejected ones with reasons.
> ([[../codex/change-verification-contract.md]])

Two concrete dogfooding episodes, both recorded in the session ledger
(`.research-notes/autonomous-session-ledger.md`), show this is real, not theoretical:

1. **The collision-aware split (2026-05-29).** A front-end build agent had finished the screen
   modules; a UX-review agent was *still running* and owned `web/pages/*.js`. The next pass
   **deliberately did not edit pages** — it committed two finished strategy docs and did a read-only
   dead-link audit instead — to avoid last-write-wins clobbering the reviewer's in-flight fixes. The
   ledger records the held punch-list to apply *after* the reviewer finishes. That is the orchestrator
   honoring an output boundary between concurrent agents — the multi-agent equivalent of the product's
   "no shared mutable state between services" rule ([[../architecture/backend-services-and-platform.md]]).

2. **The shared-front-end reversal.** The change-verification contract *exists because* this project
   once shipped a design change — a single front-end with a brand toggle — on one agent's reasoning,
   and the owner reversed it ("serious confusion between the two product surfaces"). The fix was not
   "try harder"; it was structural: design / brand / strategy / vocabulary / pricing changes now
   require **clear user intent OR strong corroboration — never a unilateral single-agent call.** The
   two products are now genuinely separate surfaces on one shared backend
   ([[../strategy/two-services-shared-infrastructure.md]]) — the corrected decision, with the dead
   shared-front-end approach superseded *in place*.

The honest version: this is *separation of duties*, not a fully autonomous swarm. The "agents" are
distinct Claude Code sessions/sub-agents with distinct write scopes, coordinated through the ledger
and the contract. The discipline — builder ≠ verifier, hold on collision, supersede in place — is what
makes concurrency safe, and it is the same discipline the product encodes between its services.

---

## 4. The measurement engine — we are scored the way components are

A component earns its place on **measured lift**, not assertion ([[../design/value-propositions.md]]).
Development changes earn their place on **measured correctness** — and the two share the
`measurement` service (`scripts/eval`, `scripts/verification`; `services/registry.yaml`), which is one
shared cost center for both products and for the build loop itself.

What the engine measures on *us*, each cycle, as a precondition for recording "done":

- **Green build** — `scripts/validate.py` on the changed paths (the fast path), or the full gate when
  schemas/vocabularies/broad references change. This is supervisor gate #1 of the six in
  [[../codex/master-goal.md]].
- **No magic values** — counts are *computed*, never typed. The README's catalog-stats block is
  generated and drift-checked (`build_readme_stats.py --check`); the canonical bug we refuse to
  reintroduce is a hand-typed component count drifting from reality
  ([[../codex/no-magic-values.md]]). This very document deliberately points at the *source* of counts
  (the foundry directory, the stats block) rather than reciting a number that would rot.
- **Self-tests** — the touched `scripts.foundry.*` / `services/*` self-test passes; web files
  `node --check`; both products' `/api/health` return 200.

The same lift discipline we apply to components is, externally, the right one: the SkillsBench "Skill
Lift" benchmark scores skills by paired with- vs without-skill performance — our exact metric — and
finds careless skills can *regress* tasks, which is why we gate (bridge:
`scripts/foundry/skillsbench.py`; [[../design/value-propositions.md]]). Corroboration that the
measured-lift bar is sound, not a house rule.

**Honest boundary.** The build loop's "measured" is *correctness* (tests/validators green) plus the
warrant; it is not, today, a single composite numeric "lift score for a docs change." For *components*,
lift is measured live only when a model route + recorded answers exist — offline, lift is computed from
recorded answers only, and **no answers + no model ⇒ unmeasured ⇒ routed to review, never invented**
([[../codex/foundry-build-loop.md]]). The foundry ledger (`data/foundry-ledger.jsonl`) is candid about
this: real partitions seeded from `data/research-queue/areas.jsonl` currently log `promoted: 0` with
`blocked: "acquisition: no source acquired … wire a scout"` — the engine refuses to promote without a
real source and a real measured lift, even when that means the day's real-partition yield is zero. The
green numbers come from the synthetic fixture and are labelled `synthetic_demo`. That refusal *is* the
product working on its own data.

---

## 5. The change-verification contract gates *this* change

Every claim in this case study is itself subject to the contract it describes. The contract requires a
**warrant** before any change is committed — evidence for *why it is correct*, not an agent's
confidence — and matches the strength of the warrant to the blast radius
([[../codex/change-verification-contract.md]]):

| Change class | Minimum warrant | This document |
|---|---|---|
| Trivial / reversible — additive doc | a principle, or self-evident correctness | ✔ additive, reversible doc |
| Substantive code — behavior/schema/API | correctness verification **and** a principle/intent | (not this change) |
| Design / brand / strategy / pricing | **clear user intent OR strong corroboration — never unilateral** | (not this change) |
| Irreversible / outward-facing | explicit intent **+** confirmation | (not this change) |

This file is an **additive doc** in the trivial/reversible row, written under **explicit user intent**
("dogfood + case studies"), and every factual claim is checked against the live repo (the foundry
self-test was *run*, not cited from memory; the ledger episodes are quoted from the ledger). The
contract's "verify before relying" rule — "a memory or doc that names a file, flag, or path is a claim
about a past state; re-check it against the repo before acting on it" — was applied while writing it.

**The honest split — automated vs human-gated.**

- **Automated (the machine does it):** the foundry funnel and evidence gate; the validators and
  self-tests; the computed stats / drift checks; the loop's ORIENT→…→REPEAT mechanics; the
  branch-on-block routing; the ledger append.
- **Human-gated (the owner decides):** design, brand, strategy, vocabulary, pricing, and product
  structure are **the owner's strategic calls** — an agent proposes and corroborates; it does not
  decide. Knowledge-Corpus components always route to a human, because "the LLM doesn't know what it
  doesn't know" and cannot self-certify its own gap (`FoundryConfig.human_approval_types` in
  `scripts/foundry/contracts.py`; public-regulation Conditionals can auto-approve). Irreversible or
  outward-facing actions need explicit intent **plus** confirmation.
- **Aspirational / not-yet-mechanized (stated plainly):** the contract's `warrant: …` ledger *tag* is
  documented and referenced by the loop commands, but the session ledger does not yet stamp every line
  with the literal prefix — the *discipline* is enforced (held/superseded decisions are recorded with
  reasons), the *uniform machine tag* is the next hardening step. A CI check that fails a commit
  lacking a warrant tag does not exist yet. We say so rather than imply full automation.

---

## What this proves (and what it doesn't)

**Proves.** The three mechanisms we sell are the three mechanisms we use. A bounded loop with grounded
inputs and an output boundary (`/evolve`), a governed memory the agent reads first (the codex + the
ledger), and a measured/warranted gate that can say *no* (the foundry's evidence gate + the
change-verification contract) — together they make an unreliable development agent dependable enough to
run for hours and branch on every block without shipping the wrong thing. The shared-front-end
reversal becoming a *structural* contract, rather than a one-off apology, is the clearest evidence the
loop learns.

**Doesn't prove.** It does not prove the platform builds itself *unattended at scale*. Design and
strategy are human-gated by design; real-source acquisition for the factory is partly blocked in the
current sandbox (the ledger shows it, honestly); the warrant *tag* isn't yet CI-enforced. Those are
named here precisely so this case study clears its own bar: **honest about what is real, what is
planned, and what is aspirational.**

The acquisition read is simple: a team that **dogfoods its own governance** — that gates its own
commits the way it gates customers' components, and records when it held a change rather than shipping
it — is a team whose moat (provenance, measured lift, signed/governed content;
[[../strategy/context-layer-pmf.md]]) is a *practice*, not a slogan.

## Related

- [[../codex/master-goal.md]] — the single canonical goal and the in-session loop the workflows run.
- [[../codex/foundry-build-loop.md]] — the runnable evidence-driven factory loop (the priority ladder).
- [[../codex/change-verification-contract.md]] — warrant-before-change; builder ≠ verifier.
- [[../architecture/evidence-driven-component-factory.md]] — the foundry's eight-stage design.
- [[../architecture/backend-services-and-platform.md]] — the shared platform the loop and both products ride.
- [[../strategy/two-services-shared-infrastructure.md]] — two products, one backend (and the reversal that shaped the contract).
- [[../design/value-propositions.md]] — measured lift, governance, freezable, open-core — the claims this loop must keep true.
