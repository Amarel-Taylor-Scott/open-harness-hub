# Using our own platform (dogfooding plan)

We build Open Harness Hub and Baltor with Claude Code over this repo. The most credible
proof that the two products solve a real problem is that **we use them on ourselves**: serve our own
governed docs into our agent, mine our own capability gaps with the foundry, run the `/evolve` loop as
the build engine, and gate every change through the change-verification contract. This doc is the
concrete adoption plan — *what works today, what needs the planned services, and the near-term step to
turn each one on.*

It is deliberately honest. Several of these are **wired and running**; one (the Baltor enrichment tier)
is `status: planned` in [services/registry.yaml](../../services/registry.yaml) and is described as a
near-term step, not a shipped capability. Where a thing is seeded-but-not-implemented, this doc says so.

**WARRANT — user-intent:** the owner asked for *acquihire prep + full docs + dogfood + use
cases/case studies/inspiration*; this is the dogfood doc. **Reinforced by an established principle:**
"If it's not in git, it didn't happen" and "no agent grades its own work"
([[../concepts/context-layer-and-the-desk.md]]) are the same disciplines this plan operationalises on
our own development. Status claims are checked against the live service map, not asserted.

## The five surfaces we adopt internally

| # | What we adopt | Which product | Runs today? | Near-term step to turn it on |
|---|---|---|---|---|
| 1 | Serve repo docs/tools to Claude Code over MCP | Baltor (delivery surface) | **Partial** — `dist/mcp/` emits today; Baltor-tiered corpus is planned | Wire a repo `.mcp.json` to the emitted server; then point it at the Baltor tier |
| 2 | Run the foundry for our own component needs | OHH backend (`foundry`) | **Yes** — `foundry` is `active`, contracts self-test passes | Seed our build-gaps into the research queue; promote on lift |
| 3 | `/evolve` loop as our build engine | Both (umbrella) | **Yes** — `.claude/commands/evolve.md` is a live skill | Pair with `/loop` or `/schedule` for unattended runs |
| 4 | The change-verification contract as our review gate | Platform discipline | **Yes** — a documented gate enforced by the verifier role | Keep tagging warrants in every commit + ledger line |
| 5 | The lift/fidelity harness as our own quality bar | `measurement` (`active`) + Baltor fidelity (`planned`) | **Lift: yes. Fidelity: seeded only** | Implement `verify.compression_fidelity` to score #1's tiers |

The through-line: **we are our own first Baltor tenant and our own first foundry customer.** Every gap we
hit building the platform is a gap to mine; every doc we feed our agent is a corpus to tier and govern.

---

## 1 · Serve our repo docs + tools to Claude Code via MCP (Baltor delivery surface)

**The goal.** Our agent (Claude Code on this repo) should get token-dense, governed, *cited* context
and callable tools dropped straight in — exactly the Baltor pitch ("serve the governed corpora + tools
into open-ended agentic workflows", [[../strategy/context-enrichment-service.md]]). Dogfooding it means
*we* are the open agent the four Baltor surfaces target: **MCP server · llms.txt · skill/plugin ·
CLAUDE.md fragment**.

**What works today.** The MCP emitter is real and runnable:

```bash
python3 scripts/emit/mcp_server.py     # → dist/mcp/{tools.json, server.py, server.ts, README.md}
```

It walks every `tool/*` and the model-safe `processor/*` components (deterministic/idempotent, no
escalation/delivery/audit side effects) and emits a working MCP server stub plus the JSON-RPC
`tools/list` response. This is the `deliver.mcp_serve` surface in component form — the same surface
Baltor sells — already producing a server from our catalog.

**What does *not* exist yet (be honest):**

- This repo has **no `.mcp.json`**, so our own Claude Code is not yet consuming that server. The
  emitter produces the artifact; nothing wires it back into our agent loop.
- The emitter serves **catalog tools**, not a **Baltor-tiered corpus of our repo docs**
  (raw → compressed → hyper-efficient). The Baltor `enrichment` service that builds those tiers is
  `status: planned` in [services/registry.yaml](../../services/registry.yaml) — its components are
  *seeded* (`scripts/seed/baltor_components.py`: `serve-mcp-corpus`, `emit-llms-txt`,
  `package-agent-skill`, `emit-claudemd-fragment`, `structural-compress`) but the tier pipeline that
  turns `docs/` into those tiers has no entrypoint.

**Near-term steps (in order):**

1. **Wire the emitted server into our own agent.** Add a repo `.mcp.json` pointing at
   `dist/mcp/server.py` so Claude Code can call our governed `processor/*` tools (e.g. the
   normalized-object extractor, the promotion planner, the codegraph query). This is the smallest real
   dogfood: our agent uses our own tools. Keep the server read-only-ish — the emitter already excludes
   escalation/audit/external-mutating kinds, which is the safe trust boundary
   ([[../concepts/context-layer-and-the-desk.md]], "treat all retrieved content as untrusted").
2. **Build the CLAUDE.md / llms.txt tier for our docs first** — these are the two *no-integration*
   surfaces and the cheapest tiers to stand up. A distilled `CLAUDE.md` fragment of our conventions
   (the vocabulary rules, the fast path, the no-magic-values rule) is the "always-loaded,
   near-zero-token" tier that must survive compaction. We already maintain a hand-written `CLAUDE.md`;
   the dogfood is to *generate* it from governed source via `deliver.claudemd` so it can't drift.
3. **Then the MCP corpus tier** — once the `enrichment` service has an entrypoint, serve our
   `docs/strategy` + `docs/codex` as a freshness-tracked, compressed corpus over `deliver.mcp_serve`,
   so the agent fetches the right governed slice instead of us pasting whole files. That closes the
   loop: **we develop the platform using the platform's own context layer.**

**Why this is the strongest dogfood.** If serving our own docs to our own agent measurably reduces the
tokens we burn re-reading files (and the fidelity harness proves the compressed tier preserved enough),
that *is* the Baltor value proposition demonstrated on the builders who'd be most skeptical of it.

---

## 2 · Run the foundry for our own component needs

**The goal.** When building the platform we repeatedly hit "the model can't reliably do X over our
repo" — find the right component for a task, route a query regex-vs-vector, dedupe near-identical
candidates. Those are *our* capability gaps. The foundry exists to turn a measured gap into a governed,
lift-proven component ([[../codex/master-goal.md]], the evidence-driven factory). Dogfooding it means we
feed **our own** build-gaps through the same gate we hold external components to.

**What works today.** The foundry is `active` ([services/registry.yaml](../../services/registry.yaml))
and its anti-filler contract is real, runnable code:

```bash
python3 -m scripts.foundry.contracts          # self-test: passes
python3 scripts/acquisition/gap_screen.py      # Stage-1 gap screen (model-independent signals)
python3 scripts/acquisition/research_queue.py  # rank owner-fed research areas
python3 scripts/eval/durable_gap_harness.py    # the lift + durability sorter
```

`scripts/foundry/contracts.py` enforces the three pillars before any candidate is minted — a measured
**gap**, a licensed **source** (`source_url` + `author` + `license`), and a measured **lift**
(`pipeline_score − bare_model_score > 0`). A cross-product clone has none, so **filler is impossible by
construction, not by cleanup.** The funnel reports `areas_probed → … → promoted`, never a flat
"generated" number — the same honest counting we owe external users.

**The dogfood loop:**

1. **Treat our build-gaps as research areas.** When a development turn stalls on "I can't find the
   component that does X," that is a candidate gap. Add it to `data/research-queue/areas.jsonl` and let
   `research_queue.py` rank it against the model-independent signals — exactly as the owner feeds
   external areas.
2. **Screen before collecting** (`gap_screen.py`) so the model can't draw its own map, then confirm on
   a sample. This is the two-stage discipline from `CLAUDE.md`, applied to our own toolbelt.
3. **Promote only on lift.** A component we build *for ourselves* clears the same gate
   (`scripts/foundry/gate.py`) — measured delta, structural durability, real source, novel. If our own
   candidate can't clear it, we don't mint it; we found a gap that isn't real, which is itself a useful
   result.

**Honest scope.** The foundry's *mechanism* runs today; whether it has *yet* produced a component we use
in our own development is a separate, measured question — do not claim it has until the ledger
(`.research-notes/autonomous-session-ledger.md`) records a promoted, lift-proven row that we then
consume. The point of this section is the **commitment to dogfood the gate**, not a shipped count.

---

## 3 · The `/evolve` loop as our build engine

**The goal.** The platform's thesis is that **narrow tasks pushed to a deterministic harness beat a
free-running model**. Our own development should run on that thesis, not contradict it. The `/evolve`
skill ([.claude/commands/evolve.md](../../.claude/commands/evolve.md)) is exactly that: a bounded,
resilient build loop — ORIENT → PLAN → BUILD → VALIDATE → RECORD → BRANCH → REPEAT — with the
capability-lift bar, the gates, and the contract baked in.

**What works today.** `/evolve` is a **live Claude Code skill in this repo.** It subsumes `/goal`
(factory), `/launch` (both surfaces + tunnels), and `/polish` (app), picking the weakest surface each
cycle. Its validation gates are the documented fast path:

```bash
python3 scripts/validate.py <changed>
python3 scripts/build_component_id_index.py --update <changed>
python3 scripts/build_catalog_pages.py --paths <changed> --update-index
python3 scripts/build_component_id_index.py --check-fresh
```

It reads the live service map and the session ledger first, so it never re-derives strategy and never
stops on a block — it switches lanes. That **is** our build engine, and there is a catalog component
that mirrors the pattern: `harness/meta-harness-evolver`
([docs/catalog/harness_meta-harness-evolver.md](../catalog/harness_meta-harness-evolver.md)) —
"propose, benchmark, compare, and safely update other harnesses using isolated branches, rollback
paths, and human review gates." We dogfood that harness by *running it on the harness hub itself.*

**Near-term step.** For unattended multi-day operation, pair `/evolve` with `/loop /evolve` (self-paced
re-invocation) or `/schedule` (a cron remote agent), as the skill documents. Each cycle appends one
ledger line; the durable memory across runs is `.research-notes/autonomous-session-ledger.md`. The
dogfood discipline is: **never report raw generated lines as active components**, and rotate lanes so no
single surface starves — the same daily-factory honesty the product demands of users.

---

## 4 · The change-verification contract as our review gate

**The goal.** Every change we ship — to the platform we sell as *governed* — must itself be governed.
The change-verification contract ([[../codex/change-verification-contract.md]]) is our review gate, and
it exists *because of a real failure on this repo*: an agent shipped a shared-front-end-with-brand-toggle
on its own reasoning and the owner reversed it. Dogfooding governance means we hold our own commits to
the warrant bar we advertise.

**What works today.** The contract is a **documented, enforced discipline** (not an automated script):
no change lands without one of three warrants — **clear user-intent**, **≥2 corroborating sources**, or
an **established repo principle** — cited in the commit message *and* the ledger. The bar is
**proportional**: a typo needs only self-evident correctness; a design/brand/strategy/vocabulary/pricing
change needs explicit owner intent and is **never a unilateral single-agent call.** In the autonomous
loop the roles separate — the prioritizer *tags* the warrant, the *verifier* (a different agent than the
builder) *confirms* it, the orchestrator commits only warranted + green items. That is "no agent grades
its own work" applied to our own changes.

**This very doc dogfoods it:** its warrant is stated at the top (user-intent + principle), it is
additive and reversible (a doc, lowest blast radius), and it touches only its assigned path. **"It's
green" is necessary, not sufficient** — that rule governs our work, not just the user's.

**Near-term step.** Keep the warrant line in every commit + ledger entry
(`warrant: user-intent — "<quote>"` · `warrant: corroboration — <sources>` · `warrant: principle —
<which>`), and let the verify step check the *warrant*, not just the build. The anti-context-rot rules
— supersede in place, verify-before-relying, one source of truth, reconcile-as-you-go — are how we keep
our own docs from drifting the way the README count once did
([[../codex/no-magic-values.md]]).

---

## 5 · The lift / fidelity harness as our own quality bar

**The goal.** The product admits components **only on measured lift**, and Baltor lives or dies on
**measured fidelity per tier** — *the same shared measurement engine, two questions* ("does the pipeline
lift?" / "did the tier preserve?", [[../strategy/context-enrichment-service.md]]). Dogfooding it means
our internal quality decisions use that engine, not vibes.

**What works today.** The `measurement` service is `active`
([services/registry.yaml](../../services/registry.yaml)); `scripts/eval/durable_gap_harness.py` sorts on
lift + durability, and the SkillsBench bridge (`scripts/foundry/skillsbench.py`) ties our **Action**
components to the field's external "Skill Lift" benchmark — paired with- vs without-skill, the same
metric, externally validated. So when we build a component *for ourselves* (section 2), we measure its
lift the same way.

**What is seeded but not implemented (be honest).** `verify.compression_fidelity` — the per-tier "did
this tier preserve enough?" evaluator that the Baltor moat depends on — exists **only as a seeded
component definition** in `scripts/seed/baltor_components.py` (`compression-fidelity-check`). There is
**no implementation** under `scripts/verification/` or `scripts/eval/` yet. Until there is, we cannot
publish a fidelity delta on the tiers from section 1 — and per our own promotion boundary
([[../codex/master-goal.md]]), an unmeasured tier is staging-only, not tenant-visible.

**Near-term step.** Implement `verify.compression_fidelity` as a real evaluator (scored by a *separate*
evaluator, never self-graded), then run it on the very first corpus we tier — our own `docs/`. That is
the dogfood that makes section 1 trustworthy: *we serve our docs to our agent at a compressed tier, and
we publish the measured fidelity delta of that tier, scored by the same engine we sell.* Recommended
substrate is the wrap-don't-rebuild pick (Braintrust / Langfuse + lm-eval-harness,
[[../strategy/recommended-stack-and-cloud.md]]).

---

## What "we use our own platform" means, end to end

The five surfaces compose into one self-hosting loop:

1. We build with **`/evolve`** (§3), the bounded engine that embodies our own narrow-task thesis.
2. Every change clears the **contract** (§4) — warranted, verified by a different agent, green.
3. When we hit a capability gap, the **foundry** (§2) turns it into a lift-proven component — or proves
   the gap isn't real.
4. The **measurement** engine (§5) scores that lift the way the product promises; the fidelity half is
   the near-term build that unblocks the tiers.
5. Our own governed docs flow back to our agent through the **Baltor delivery surfaces** (§1), so we
   develop the platform *using the platform's context layer.*

**The honest scorecard.** Today: `/evolve`, the contract, the foundry mechanism, the lift harness, and
the MCP emitter all run. The gaps to close — each a near-term step above — are the **`.mcp.json` wiring**,
the **Baltor tier pipeline entrypoint** (`enrichment` is `planned`), and the **`verify.compression_fidelity`
implementation**. None forks the backend; each is a deployment of code that already lives in `scripts/`.
When all five run on us, "two products, one backend" stops being an architecture diagram and becomes our
own daily workflow — which is the most credible thing we can show an acquirer or a user.

## Related

- [[../strategy/two-services-shared-infrastructure.md]] — the two-products/one-backend decision.
- [[../strategy/context-enrichment-service.md]] — the Baltor spec (the four delivery surfaces, the tiers).
- [[../codex/change-verification-contract.md]] — the review gate (§4).
- [[../codex/master-goal.md]] — the capability-lift bar and the evidence-driven foundry (§2).
- [[../concepts/context-layer-and-the-desk.md]] — the context-layer model §1 serves us through.
- [services/registry.yaml](../../services/registry.yaml) — the live `active`/`planned` service map.
- [.claude/commands/evolve.md](../../.claude/commands/evolve.md) — the build-engine skill (§3).
