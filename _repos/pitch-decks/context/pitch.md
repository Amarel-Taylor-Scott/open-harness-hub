# The acquihire pitch — OpenHubForAI + Baltor (PRIVATE)

> **What this is.** The strategic *narrative* for a single acquirer conversation — a model
> lab, a hyperscaler, a data-platform, or a dev-tools company. It is the story (the wedge,
> the moat, why a team+tech buy), not the build plan. The execution plan lives in
> [[acquihire-roadmap]] (90-day arcs, gap analysis, per-acquirer leads); the older
> single-product brief is [[acquisition-positioning]]; the market thesis is
> [[context-layer-pmf]]. This page sits above all three and frames the conversation
> around the **two-doors-one-backend** structure that those three predate or only touch.
>
> **Honesty rule (non-negotiable).** Per [[../../codex/change-verification-contract]], every
> claim here is tagged **REAL** (committed code / computed stat / passing self-test),
> **SPEC** (designed, boundary defined, no running entrypoint), or **NEXT** (not built).
> No generated/aspirational number is ever presented as shipped. Counts are computed
> ([[../../codex/no-magic-values]]); where a number isn't known, it says so.

---

## 1. The one paragraph

We are building the **open, governed context layer** for AI — the layer that decides
*which* facts reach a model, proves they *lift* its capability, and keeps them *fresh and
attributable* — and we sell it through **two doors over one backend**. Door one,
**OpenHubForAI**, lets a builder assemble and monitor a bounded, governed *pipeline*.
Door two, **Baltor** (Baltor), refines a corpus into token-efficiency tiers and
serves it — measured-fidelity-per-tier — straight into any open agent (Claude Code, Cursor,
any MCP client). The two doors consume *the same governed object*: a Knowledge Corpus or
Action minted once, with one provenance trail and one measurement. The thing a bigger model
cannot copy is not the components — it's the **governance + measured-lift + composability**
substrate underneath them. That substrate is what an acquirer buys, and it is *anti-fragile
to model progress*: the better the model, the tighter we focus on what it still can't do
reliably.

---

## 2. The market we're standing in (and why now)

The public tape already validated the category. The Q1-FY27 prints from Snowflake (product
rev $1.33B, +34%), MongoDB ($687.6M, +25%, Atlas +29%), Datadog (+32%), and Cloudflare
(+34% on agentic) tell one story: a **consumption-priced "context layer."** AI doesn't
replace the data platform — it feeds it more work (retrieval, memory, real-time signals,
governance), billed per query / per GB / per inference. (Full citation chain:
[[context-layer-pmf]].)

But the named winners sell *infrastructure* (a data platform, a vector DB, an observability
pipe), and the open frameworks (Mem0, Zep, Letta, LlamaIndex, LLMLingua, GPTCache) give you
*plumbing*. The builder-side research says where both fall short, in their own words:
*"these frameworks generally lack enterprise governance — no glossary, lineage, or entity
resolution, which is precisely the seam the commercial context-layer vendors are selling
into."* And Gartner's read on the protocol layer: *MCP moves context, it does not produce
it* — 60% of MCP-only agentic projects are projected to fail by 2028 without a consistent
layer beneath ([[recommended-stack-and-cloud]]).

**That seam is us.** Not another vector DB or memory lib — the **governed assembler** that
wraps Qdrant/Mem0/LLMLingua as measured-lift, provenance-bearing, composable components
under one eval contract. The substrate is the commodity; *lift + governance + composability*
is the layer nobody hosts.

---

## 3. The wedge — governed context, measured

Two faces, one guarantee. Both are admitted only on **measured** value, never asserted.

- **OpenHubForAI** sells governed **pipelines**. A component earns its place by one rule:
  it must **lift capability over a bare LLM** — `pipeline_score − bare_model_score > 0` on a
  real task — *and* that lift must be **structural** (it won't close when the next model
  ships). The single source of the durability taxonomy (`lift_reason → durability_class`) is
  `scripts/eval/reason_codes.py` — six structural reasons (volatile fact, no addressable
  source, accountability/license, deterministic guarantee, closed-channel access,
  tacit/embodied knowledge), never re-defined elsewhere. **[REAL]**
- **Baltor** sells governed **fuel**. It refines content into three tiers —
  raw → compressed → hyper-efficient — each a *different mechanism* (structural body-strip,
  learned token-classification, distilled-facts-on-a-cacheable-prefix), and ships every
  artifact with a **published fidelity delta** scored by a *separate* evaluator:
  "did this tier preserve enough?" Compress too hard and you destroy the model's ability to
  reason — so measured fidelity *is* the product, not a footnote ([[context-enrichment-service]]).
  **[SPEC — components seeded `scripts/seed/baltor_components.py`; tier pipeline NEXT.]**

The crux: **the fidelity gate and the lift gate are the same measurement engine.** One asks
"did the pipeline lift?", the other "did the tier preserve?" — same harness, same separate-
evaluator discipline, same moat. That is why one backend serving two doors isn't just COGS
economy; **it's one moat sold through two doors.**

---

## 4. The structure — two doors, one backend (the part that's distinctive)

This is the core of the pitch and the thing the older briefs predate. We run **two products
on two domains** sharing **one infrastructure plane** — clusters, workers, the engine, the
component+corpus data plane, governance. *One COGS, two revenue lines.* (Decision record:
[[two-services-shared-infrastructure]]; backend topology: [[../../architecture/backend-services-and-platform]].)

```
   builders ──▶  OPEN HARNESS HUB            CONTEXT ENRICHMENT  ◀── agent devs
                 (bounded: assemble DAG,      (unbounded: ingest,    (Claude Code,
                  run/trace, I/O rules,        tier raw→compressed→   Cursor, any
                  monitor + LIFT gate)         hyper-efficient,       MCP client)
                  sells: governed PIPELINES    host/serve)
                                               sells: governed FUEL
                          │     two doors, one object     │
                          ▼                               ▼
                  ── THE JOIN: a Knowledge Corpus / Action minted ONCE,
                     one provenance trail, one lift + fidelity score ──
                          │
                          ▼
   ── SHARED PLATFORM PLANE ──
      compute (K8s · vLLM) · engine (foundry + MEASUREMENT) · ingestion ·
      storage (object store · pgvector · tiered artifacts) · governance (provenance/
      AIBOM · citations · CDC/freshness) · billing (per query · per GB · per refresh)
```

Why this is a stronger acquisition story than either product alone:

1. **Two proven GTM motions onto one substrate.** *Build-a-pipeline* (applied/regulated
   teams) **and** *enrich-any-agent* (the far larger pool of anyone running Claude Code or
   open agents at scale). The acquirer gets the context-layer substrate *plus* two distinct
   distribution surfaces onto it.
2. **Every component is sellable through either door.** A corpus minted for an OHH pipeline
   is instantly Baltor fuel; a compressor built for Baltor is instantly an OHH component. The
   data plane is **attribute-level, not column-level** ([[../../codex/schema-extensibility]]):
   a facet added for one door is a row the other door reads — never a per-service column.
   **[REAL — principle enforced in the schema.]**
3. **A feature shipped for one is instantly the other's.** A better compressor, a fresher
   corpus, a new tool — built once, live on both surfaces. The expensive parts are *one set,
   shared*; only the two thin storefronts and the billing meters differ.

This is **not** one app with a brand toggle — an earlier draft framed it that way and the
owner reversed it ("serious confusion between the two product surfaces"); that reversal is
why the [[../../codex/change-verification-contract]] exists. The two services are genuinely
distinct surfaces on a shared substrate.

---

## 5. The moat — governance + measured-lift + composability

Three things, orthogonal to model quality, that a bigger model supplies *none* of:

- **Governance is the external moat.** Provenance on every fact, signed/verified publishers,
  live corpora with CDC freshness + revocation, an accountable signer, auditor-grade
  attestation (SPDX 3.0 · C2PA · EU AI Act Annex IV · CycloneDX-ML · OpenLineage emitters).
  This is exactly what regulated buyers pay for and exactly what raw infra and open
  frameworks lack. **[REAL — 13 emitters under `scripts/emit/`; live operation is NEXT.]**
- **Measured lift is the internal selection criterion.** It is *not* our assertion. The
  field published the same metric: **SkillsBench / Skill Lift** (BenchFlow, Kaggle May–Jul
  2026; arXiv:2602.12670, arXiv:2604.05172) measures with-skill-minus-without lift plus an
  adversarial safety gate — a one-to-one map onto our admission rule
  ([[skillsbench-alignment]]). Their headline is our whole reason to exist: **+16.4pp
  average lift across 84 expert tasks — but 18 of 84 get *worse*, and skills a model writes
  for itself net −1.3pp.** A component can lift, do nothing, or quietly break — so it must be
  *measured*, by a separate evaluator, and LLM-self-authored components route to human
  approval. We export every Action to a submittable `SKILL.md` today.
  **[REAL — bridge `scripts/foundry/skillsbench.py` self-test passes; an actual submission is NEXT.]**
- **Composability under one grammar.** Seven primitives — Input · Knowledge Corpus ·
  Conditional · Action · Loop · Stop/End · Output — let any component wire (and swap) into a
  governed flow, and most of the lift is **freezable** (Conditionals, rule-packs, retrieval,
  citation gates freeze into the export; you pay model cost only for the one or two real
  Action calls). "More lift, the bill barely moves." **[REAL — grammar + export emitters.]**

The synthesis: **the better the model, the more valuable this gets.** The lift gate prunes
anything a stronger model absorbs and re-parks the catalog on the moving frontier; the
governance moat is untouched by model quality; the measurement dataset compounds with every
run ([[acquisition-positioning]] "anti-fragile to model progress").

---

## 6. What an acquirer actually buys (team + tech)

A clean, focused substrate whose assets compound as base models improve:

1. **The measurement dataset** — `bare_vs_pipeline` (and tier-fidelity) deltas across real
   tasks: a scarce, model-improving eval/post-training signal mapping *exactly* where
   grounded pipelines beat bare models. Uniquely valuable to a lab; licensable on its own.
2. **The governed fresh-fact flywheel** — scrapers + CDC + provenance + signed publishers
   producing dated, verifiable, continuously-refreshed knowledge. It decays the moment a
   user disconnects — which is why it is *both* recurring revenue and a durable asset.
3. **The open standard + community** — an open protocol/engine for describing, validating,
   running, and composing components; ecosystem lock-in at the *format* layer (the Hub is the
   canonical index others publish into).
4. **The foundry** — an evidence-gated generation engine (computed: **21 self-tested
   modules** in `scripts/foundry/`) that mints a component *only* with a measured gap, a real
   licensed source, and a measured lift, with human approval on knowledge. Filler is
   impossible by construction. **[REAL — `python -m scripts.foundry.pipeline --self-test` passes.]**
5. **The demand graph** — privacy-redacted interactions → unmet-need signal → prioritized
   build queue: a model-independent map of what the market needs next.

And the **team**: the discipline behind these assets — the capability-lift bar, the
two-axis durability gate, the no-magic-values / change-verification contracts, the
governance spine — is a way of building that ports directly into a lab's safety- and
eval-native culture.

---

## 7. The open-core on-ramp

The wedge is also the funnel. **Open / free / Apache-2.0:** the spec, the seven-primitive
grammar, the SDK/CLI, the export emitters (SPDX/C2PA/JSON-LD/EU-AI-Act), and externally
verified public knowledge. **Commercial / recurring:** the vetted measured-lift components,
the live governed corpora kept fresh with CDC, build-on-demand, hosted/metered queries, and
attestation renewal — the billing axes are *already consumption-shaped* (per assembled flow,
per governed-corpus refresh, per metered retrieval call), the same per-query/per-GB motion
the public market rewards ([[context-layer-pmf]]). The pricing boundary falls out of the
architecture: **raw + compressed are freezable** (download, one-time/storage); **hyper-
efficient, served live and kept fresh, is recurring** — a static download can't stay current,
and that CDC/freshness obligation is the recurring-revenue moat. **[REAL — billing axes
implemented `scripts/foundry/access.py`; Stripe + meter-at-worker is NEXT.]**

---

## 8. What's real vs next (honest)

The same daily contract the product enforces — report *promoted*, never *generated* — applies
to this pitch's own status. Detailed gap analysis: [[acquihire-roadmap]] §2.

| Asset | Status | Evidence (computed / committed) |
|---|---|---|
| Capability-lift bar + durability taxonomy | **REAL** | `scripts/eval/reason_codes.py` (single source); lift gate report `dist/reports/capability-lift-gate.json`: floor **0.2**, **kept 2,397 / culled 1,980** of **4,377** — the gate visibly rejecting filler. |
| The foundry (evidence-gated generation) | **REAL** | **21 self-tested modules**; `--self-test` passes incl. "anti-filler: every promoted row is fully evidenced." |
| Catalog (database-backed, computed counts) | **REAL** | Counts are **computed at build** by `scripts/build_readme_stats.py` (shown in the README, never hand-typed — see `docs/codex/no-magic-values.md`): schema-validated manifests, of which a fraction are committed and the rest machine-generated candidates pending review, plus those loaded into the derived query DB. *Candidates are not shipped components — cite the live build output, not a frozen integer.* |
| Two-product structure + shared plane | **REAL (design) + SPEC (deploy)** | Decision record [[two-services-shared-infrastructure]]; both product surfaces exist (`web/harness-hub/`, `web/baltor/`); `services/registry.yaml` is the map. The `enrichment` *platform service* is `status: planned`; the shared K8s/worker deploy is NEXT. |
| Governance emitter surface | **REAL (emit) + NEXT (operate)** | 13 emitters incl. C2PA/SPDX 3.0/EU-AI-Act Annex IV; running scrapers on a cadence + CDC/revocation + signing keys are NEXT. |
| Measured lift, in the wild | **REAL (one instance), thin** | One canonical **+1.0** freshness lift (stale answer → fresh dated, provenance'd fact, live via Ollama). A lift *distribution* across families is the flywheel's job — not yet at volume. |
| SkillsBench external proof | **REAL (bridge) + NEXT (submission)** | `scripts/foundry/skillsbench.py` self-test passes; catalog is submittable today; an actual Skill Lift submission is NEXT. |
| Baltor tiers / surfaces / fidelity | **SPEC** | Governed component definitions seeded (`scripts/seed/baltor_components.py`); the tier pipeline, the MCP serving endpoint, the four emitters, and the fidelity meter are NEXT. |
| **Real embeddings** (hybrid search) | **NEXT — the #1 blocker** | README computed stat: **0 embeddings** in `dist/catalog.sqlite`. Unblocks hybrid retrieval + the promotion vectorization gate. Cheapest, highest-leverage next step. |
| Stripe / auth / tenancy / cloud deploy | **NEXT** | Billing axes + auth UI exist; payment processor, backend identity, tenant isolation, and the Phase-1 cloud deploy are unbuilt. |

The honest read: **the substrate and the discipline are real and self-tested; the moat's
mechanics are implemented at the emitter/billing-axis layer and proven once (+1.0); the gaps
are operational** — embeddings, the live governed layer, billing plumbing, and the shared
cloud deploy. None of them forks the backend.

---

## 9. The ask, framed per acquirer

The pitch is *identical* to every acquirer — *"the better the model, the tighter we focus on
what it still can't do"* — and what changes is **which asset leads the first slide**
([[acquihire-roadmap]] §4 has the full per-acquirer build, demo, and metric):

- **Model lab (Anthropic / OpenAI):** lead with **the measurement dataset + the safety gate**.
  A model-independent map of where grounded pipelines beat bare models — a post-training and
  product-prioritization signal — and a registry that adds capability *without* a safety cost
  (SkillsBench's ClawsBench maps onto our gate + human-approval-by-design).
- **Hyperscaler (Google):** lead with **the governed fresh-fact flywheel + BYO-cloud/air-gap**
  — the regulated-enterprise governance story deployable in the customer's VPC.
- **Data-platform / context-layer incumbent:** lead with **the governed assembler at the seam
  raw infra leaves open** — the lift + governance + composability layer on top of their store,
  and Baltor as the open-agent distribution surface ([[context-layer-pmf]]).
- **Dev-tools (GitHub / Microsoft):** lead with **the open standard + the foundry as a
  registry/CI primitive** — paste a task → costed, deployable, SPDX/C2PA-attested bundle →
  export to a repo + CI. The "Docker-Hub-for-pipelines" framing.

The common thread, and the reason this is a *team + tech* acquisition rather than a feature
buy: the assets that make the acquisition obvious — the measurement dataset, the governed
flywheel, the foundry, the open standard, the demand graph — are the *same* assets that run
the business, built by a team that builds the way a lab needs to build.

---

*Grounds / warrant: **user-intent** — the owner directed acquihire prep framed around the
two-products-one-backend structure and the context-layer thesis (the operating brief, and the
recorded owner decisions captured in [[two-services-shared-infrastructure]] and [[context-layer-pmf]]).
**Established principle** — [[../../codex/master-goal]] (the lift bar), [[../../codex/change-verification-contract]]
(the honesty rule this page obeys), [[two-services-shared-infrastructure]], [[context-layer-pmf]],
[[context-enrichment-service]], [[../../design/value-propositions]]. **Corroboration** — the
SkillsBench/ClawsBench papers and the public-market prints cited inline in [[context-layer-pmf]]
and [[skillsbench-alignment]]. All status tags computed/verified against `scripts/foundry/`
(21 modules), `dist/reports/capability-lift-gate.json`, README computed stats, and
`services/registry.yaml`.*
