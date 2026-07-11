# The Overarching Goal — the single mission a component owner reads first

> This is the consolidated north star for the whole portfolio. It summarizes and
> links to the detailed source docs; it does not replace them. If a number would
> appear here, this doc cites the doc or record that computes it — no count is
> hand-typed (per the No-Magic-Values law in `CLAUDE.md`).
>
> **Single entry point:** the operational entry-point goal an agent executes is
> [`codex/master-goal.md`](codex/master-goal.md) (the long-horizon program); this doc is its one-page
> mission summary and points to it. **Path convention:** short-form citations resolve to the canonical
> multi-repo layout — `docs/`, `scripts/`, `architecture/` live under `_repos/shared-backend-components/`;
> `src/teleon/…` under `_repos/teleon/backend/`; `src/baltor/…` under `_repos/baltor/backend/`.
>
> **Canonical sources this doc consolidates (read them for depth):**
> `docs/BIBLE.md` §0–§2 (north-star vision + brand pillars), `CLAUDE.md`
> (North Star + "The Foundational Law"), `architecture/substrate_layers.json`
> (`foundational_law` + the layer map), `docs/strategy/north-stars.md`, and
> `docs/concepts/component-taxonomy-and-stages.md` (the seven primitives).
> If this doc ever disagrees with `docs/BIBLE.md`, the BIBLE wins
> (`docs/BIBLE.md`, top matter).

---

## 1. What we are building

We are building a **systems layer for executable capability** — not point
products (`docs/BIBLE.md` §0; `CLAUDE.md` "The Foundational Law";
`architecture/substrate_layers.json` → `principle`). Four roles operate over one
substrate:

- **Teleon** — indexes and optimizes the capability; the purpose-driven,
  eval-gated, self-adaptive compute **runtime** (`docs/BIBLE.md` §2, pillar
  Teleon; domain `teleon.dev`).
- **Baltor** — governs its **truth**; the managed, verified, provable context
  product, powered by Teleon as a tenant (`docs/BIBLE.md` §2, pillar Baltor;
  domain `baltor.ai`).
- **OpenHubForAI** — structures the open knowledge; the open **store** both
  products consume plus the open CapabilityTask spec (`docs/BIBLE.md` §2, pillar
  OpenHubForAI; one site, `OpenHubForAI.io`, per `docs/BIBLE.md` §4).
- **AIDevObserver** — watches AI **usage**; post-session review plus
  intra-session coaching (`docs/BIBLE.md` §2, pillar AIDevObserver; engine
  `src/teleon/observer`).

All four sit under the holding brand **AI Done Right** (`aidoneright.dev`,
tagline "AI, done right." — `docs/BIBLE.md` §1). They are bound by one
dependency law: **Baltor → Teleon → OpenHubForAI, never the reverse**, enforced
by `scripts/check_portfolio_dependency_law.py` over
`architecture/portfolio_dependency_law.json` (`docs/BIBLE.md` §3). Consumption
flows up; dependency points down.

Concretely, the thing being indexed, governed, structured, and watched is a
**database-backed registry of reusable AI pipeline components and
subcomponents** that scales without turning every row into a static page — a
component network spanning pre-LLM stages (intake, OCR, normalization, source
governance, entity linking, dedupe, routing, cost gates), LLM/model stages
(local models, hosted routes, browser models, embeddings, rerankers, training
jobs, multimodal generators), post-LLM stages (verification, scoring, review
queues, change-data-capture propagation, signed publisher updates, deployment
blueprints), and the runtimes underneath (`CLAUDE.md` North Star). Product
vocabulary is fixed: **Knowledge Corpus**, **If Statement**, **Action**;
"components" and "subcomponents" in new prose; version lives in metadata, never
in a name or id (`CLAUDE.md` North Star; Deterministic Global Object Naming).

---

## 2. The primitive substrate — the seven-primitive model

The substrate everything reduces to is **seven primitives**, each extending one
generic shell (`scripts/primitives/base.py::Primitive`, contract `run(po) -> po`),
one file per primitive under `scripts/primitives/`. Every catalog component
`type` is a subtype of exactly one primitive
(`docs/concepts/component-taxonomy-and-stages.md`, "The seven primitives"):

1. **Input** — the payload to work on.
2. **Knowledge Corpus** — a store of facts, queried by a trigger.
3. **If Statement** — the condition (the IF), kept separate from the THEN.
4. **Action** — anything that *does* something (the THEN): persona, tool,
   processor, harness, adapter, rubric, benchmark.
5. **Loop** — control flow / iteration over sub-steps.
6. **Stop / End** — halt early on a guard or terminal condition.
7. **Output** — finalize the result plus trace.

There is **no eighth primitive.** An unmet need is captured as a
**capability-request** — a typed empty slot carrying the `target_type` it will
become and the maturity tier `abstract`, never tenant-visible as a component
(`docs/concepts/component-taxonomy-and-stages.md`, "Not an eighth primitive";
`schemas/capability-request.schema.json`). Role (which of the seven) and
maturity (`abstract` < `experimental` < `beta` < `stable`) are orthogonal axes.

The finer atomic operations below the seven — a first-class registry of ~25
atomic ops and per-software decomposition — are a named, partial gap, not yet
complete (`architecture/substrate_layers.json` → layer `computational_genome`,
`real_gap`; existing assets `architecture/fundamental_primitives_taxonomy.json`,
`src/teleon/knowledge/code_genome.py`).

---

## 3. The reconciled filters that govern what we build

`docs/BIBLE.md` §0 states these as five; the single source is
`architecture/substrate_layers.json` → `foundational_law`. The task-canonical
four are the load-bearing gate for any new work; the fifth (recursive
improvement) is the governor that keeps the four self-revising rather than static.

1. **System filter** — *Does this improve compiler intelligence?* If no, do not
   build it. Governs what WE build.
   (`architecture/substrate_layers.json` → `foundational_law.system_filter`.)
2. **Execution filter (descent)** — *Can intelligence be removed from this
   execution path?* Descend toward that forever: make-it-work → make-it-cheap →
   deterministic substitution.
   (`foundational_law.execution_filter`.)
3. **Component admission (two-axis)** — a component must **lift** over the bare
   model (`pipeline_score − bare_model_score > 0`) **and** the lift must be
   **structural / durable** — it will not close when the next model ships.
   Governs what enters the registries. Single source of the reason-code / durability
   taxonomy: `scripts/eval/reason_codes.py`; concept: `docs/concepts/capability-valleys.md`;
   sorter: `scripts/eval/durable_gap_harness.py`
   (`foundational_law.component_admission`; `docs/strategy/north-stars.md` §2).
4. **Binding constraint — DEPTH BEFORE BREADTH** — every new layer must serve the
   ONE vertical being proven to a paying customer; breadth without a proven
   revenue vertical is the named failure mode. Gated by
   `scripts/proposal_backlog.py`
   (`foundational_law.binding_constraint`; see §4 below).

**The governor (fifth filter) — recursive improvement:** nothing is static.
Every object can be challenged, every architecture can mutate (versioned rewrite
under regression-gated rollback), every distillation must rehydrate losslessly,
every harness can evolve as the frontier moves; every failure triggers diagnosis
→ a versioned improvement, never a silent patch. But improvement is **governed**:
it still must pass filters 1–4 and the **Lossless Distillation Clause** — a
mutation is a NEW versioned layer; the prior layer, lineage, and rollback target
survive (`architecture/substrate_layers.json` →
`foundational_law.recursive_improvement`; `docs/codex/lossless-distillation.md`).
Reconciliation, in the manifest's words: filter 1 selects what we build, filter
3 selects what enters the registries, filter 2 is the descent, filter 4
subordinates all of it to depth/revenue, and the fifth makes the whole thing
self-revising — the owner's law is necessary, the pre-existing laws make it
sufficient (`foundational_law.reconciliation`).

**Before building any "new" layer, check it does not already exist.** Most of the
owner's proposed "missing layers" turned out to be partial-or-live in the repo
(`architecture/substrate_layers.json` → `layers[*].status`, checked by
`scripts/check_substrate_layers.py`). Run `scripts/check_substrate_layers.py`,
`scripts/codegraph.py --audit`, and the reinvention guard first. *"This already
exists, do not rebuild it"* is the highest-ROI decision in the architecture
(`CLAUDE.md` "The Foundational Law").

---

## 4. The binding constraint, made concrete

**Depth before breadth** is not a slogan; it is the one filter that outranks the
others when they conflict (`architecture/substrate_layers.json` →
`foundational_law.binding_constraint`; `docs/BIBLE.md` §0). Scale is the ambition
— the intent is a registry that grows from thousands to millions to far more
rows (`CLAUDE.md` North Star; daily factory targets in `CLAUDE.md` "Daily
Factory Target") — but scale is earned by first proving ONE vertical to a paying
customer. The corollary north stars that make one vertical defensible
(`docs/strategy/north-stars.md`):

- **Negative space, not the head** — build the corpus where base models are weak,
  selected by external signals and a measured coverage map, never model priors
  (`north-stars.md` §1; `docs/strategy/corpus-acquisition-grid-spec.md`).
- **Screen before you collect** — cheap Stage-1 gap screen over the whole net →
  expensive Stage-2 confirm on a thin sample → scale only confirmed gaps
  (`north-stars.md` §3; `scripts/acquisition/gap_screen.py`).
- **Governance/provenance is the product** — the lift bar is the internal
  selection criterion; the chain of custody, license audit, revocation, and
  accountable signer are the external moat regulated buyers pay for
  (`north-stars.md` §4).
- **Maintenance > acquisition** — every fact carries source, retrieval time,
  effective date, version, and supersedes links; the change-data-capture /
  re-harvest / revocation loop is the recurring differentiator
  (`north-stars.md` §5).

Owner-stated value propositions the one vertical must demonstrate: **valleys**
(capability where base models are weak), **streamlining** (paste a task → a
deployable, costed pipeline), **cost savings** (gates, routing, cheaper models on
narrow scopes), and **tracking** (provenance, freshness, change-data-capture,
decay signals) (`north-stars.md`, "Value propositions").

---

## 5. Non-negotiable rails a component owner works under

- **Warrant before change** — every change carries a warrant (clear user intent,
  ≥2 agreeing sources, or an established repo principle); match the bar to the
  blast radius; "it's green" is necessary, not sufficient
  (`CLAUDE.md` "Change Verification"; `docs/codex/change-verification-contract.md`).
- **Distillation is never replacement** — any distillation/compression/promotion
  creates a new versioned derived layer and preserves the raw layer, lineage, and
  a rollback target (`CLAUDE.md` "Lossless Distillation";
  `docs/codex/lossless-distillation.md`).
- **Archived, never deleted** — superseded context moves to
  `archive/legacy/<original-path>` with a status label, never untracked
  (`CLAUDE.md` "Archived / Legacy Files").
- **No magic values** — repo-describing numbers are computed, not typed; a value
  used in more than one place gets one definition (`CLAUDE.md` "No Magic
  Values"; `docs/codex/no-magic-values.md`).
- **Deterministic global naming** — every defined thing gets a globally unique,
  location-derived, meaning-bearing name; version lives in metadata, never in a
  name or id (`CLAUDE.md` "Deterministic Global Object Naming").
- **Promotion boundary** — candidate load-readiness is not tenant-visible
  publication; open review tickets, high-risk requirements, placeholder
  embeddings, or unresolved source/signature questions block promotion
  (`CLAUDE.md` "Promotion Boundary").
- **Safety and scope** — no real PII/secrets; synthetic or public metadata only;
  do not republish `_reference/`; no new insurance pipelines; prefer review
  queues, verified facts, signed publishers, and deterministic gates over "just
  ask the model" (`CLAUDE.md` "Safety And Scope"; `north-stars.md`, "Safety
  stance").

---

## 6. Where to go next

- The full vision, the five brand pillars, the OpenHubForAI surfaces and
  registries, and the binding laws: **`docs/BIBLE.md`** (the north-star reference
  — if any doc disagrees with it, it wins).
- The agent operating layer (fast path, code-graph audit, factory targets):
  **`CLAUDE.md`**.
- The reconciled filters plus the layer-by-layer map of proposed layers vs. what
  already exists: **`architecture/substrate_layers.json`** (checked by
  `scripts/check_substrate_layers.py`).
- The strategic north stars (negative space, two-axis admission, screen,
  governance moat, maintenance): **`docs/strategy/north-stars.md`** (its own
  canonical master goal is `docs/codex/master-goal.md`).
- The primitive substrate and component taxonomy:
  **`docs/concepts/component-taxonomy-and-stages.md`** and
  **`docs/concepts/capability-valleys.md`**.
