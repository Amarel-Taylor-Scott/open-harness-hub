# Baltor / AI Done Right (founding thesis: Context is Everything) — YC Master: Current State · Scale · Business Plan · Pitch

**Status:** consolidating master (additive). **Date:** 2026-06-06.
**Purpose:** one artifact that ties together (1) where we actually are, (2) the cloud/API/cloud-function
toolkit + the horizontally- and vertically-scalable demo, (3) the business plan, and (4) the YC pitch deck.
It **references**, and does not duplicate, the canonical strategy docs — when they disagree with this doc,
the source-of-truth is named inline. Anything that is a **proposal needing an owner decision** (pricing,
raise size, TAM math) is flagged `⟦DECISION⟧`. Brand is **LOCKED** per `brand-architecture.md` — this doc
uses it verbatim and never re-opens it.

> **Canonical inputs** (read these for depth): `docs/strategy/brand-architecture.md` (identity, LOCKED) ·
> `docs/strategy/baltor-cloud-cost-pricing-pro-forma.md` (cost + pricing + pro forma, authoritative) ·
> `docs/strategy/baltor-gtm-fundraising-plan.md` (GTM) · `docs/strategy/context-layer-pmf.md` (TAM/PMF) ·
> `docs/strategy/competitive-landscape-2026.md` + `competitive-positioning-deep-dive.md` (competition) ·
> `docs/workers/execution-backend-flexibility.md` (cloud/function toolkit) ·
> `architecture/external_capability_catalog.json` (the swappable-tool surface) ·
> `prompts/baltor-north-star-continuous-builder.md` (the engineering North Star).

---

## 0 · The one-liner (LOCKED brand, use verbatim)

- **Thesis hook:** *Models don't fail. Their context does.*
- **Functional:** *Verified, current, and provable context for the agents you already run.*
- **Soul:** *Trust your context like Nome trusted Balto.*
- **Pillars:** **Verified · Current · Efficient · Provable.**

**Company:** AI Done Right (founding thesis: Context is Everything). **Paid SaaS:** **Baltor.ai** (modules: **Verify · Corpus · Compress**,
with proof built into all three — not a separate SKU). **Open funnel:** **Open Harness Hub** (free; build the
governed workflow that consumes Baltor). One backend; the join is *one governed object, two doors*.

---

## 1 · Current state (the honest technical truth)

We are **pre-revenue, design-partner stage**. The asset is not traction — it's a **working, governed context
engine that already runs end-to-end, offline, deterministically, with the moat mechanics built in**. That is
unusual for pre-seed and it is the thing to lead with.

### 1.1 What is *real and proven* (runs today, with a deterministic self-test)

| Capability | State | Proof / anchor |
|---|---|---|
| Six-stage governed engine (Source → Reconciliation → Anti-Fragility → Enhancement → Optimization → Consumption) + a universal **Verification rail** | **working** | `scripts/demo_offline_full_baltor.py --self-test` |
| **CFPB correctness invariant** (end-to-end): answer = "10 business days" (Reg-E wins by authority); the 30-day FAQ held out; narrative allegations held out; only the reconciled winner served; lineage + receipt on everything | **working, always-on** | `check_offline_full_demo`, `check_contextops_cfpb_reference` |
| **OFAC sanctions** connector — deterministic + a synthetic-fixture conformance test (always-green) **AND a dated live catch**: a 2026-06-14 `--live` run against the real OFAC SDN list (the real 19,065-row source list, hash `e30f6077`; this dated run parsed a 5-row `--limit` sample) caught a *planted* would-be violation — a SYNTHETIC internal claim asserting CLEAR on a currently-designated entity (program CUBA), held out of the served corpus (the clearing claim is the demo's adversarial test input; the live SDN fetch + hash are real). Receipt: `docs/strategy/evidence/ofac-live-run-2026-06-14.json` | **working** | `--self-test` (offline) · `--live --demo` (dated run) |
| Recursive **document decomposition** (1,000-page proven), atomic facts vs held-out allegations | **working** | `scripts/ingest/document_decompose.py --self-test` |
| **Worker fleet**: durable SQLite ledger, atomic claim (`BEGIN IMMEDIATE` = Postgres `FOR UPDATE SKIP LOCKED`), leases, retry/DLQ, idempotency, dependency ordering | **working, cross-process** | `check_durable_fleet_ledger`, `check_worker_fleet_supervisor_full_stack` |
| **Live supervisor scaling**: leader/shard leases, two-process failover, no duplicate scheduling | **working** | `check_live_supervisor_two_process`, `…_full_stack` |
| **Execution-backend flexibility**: any task runs on local-function-emulator / subprocess / k8s / k8s-Job / Cloud Run / Lambda / Azure-Function — chosen by **policy + pricebook + health**, switchable, reversible, cloud-deferred-never-blocking | **wired live** | `check_live_fleet_execution_backend_wiring`, `/api/fleet/execution` |
| **Determinism Factory** (expensive LLM/agent resolution → distilled deterministic rule, lossless) + **ContextOps Verification Foundry** (agents PROPOSE, Baltor DISPOSES) | **working** | `check_cfpb_reconciliation_rule_distillation`, ContextOps proofs |
| Native-format preservation + governed sidecars; temporal fact graph; context-rot/freshness CDC; memory-as-candidate-context (never truth) | **working** | respective `check_*` proofs |
| **Governance spine**: every served fact has source handles + receipt + lineage; promotion boundary (candidate ≠ tenant-visible); LLM/agent/memory/browser output is never truth | **enforced by proofs** | the no-bypass / no-truth redteam proofs |

**Deterministic proof count (computed, recompute with `python3 -c "from scripts.flywheel_proof_modules import PROOF_MODULES; print(len(PROOF_MODULES))"`):** **⟦computed: 518⟧ green** as of 2026-06-20. A stdlib-only Python 3.14 watchdog re-runs all ⟦computed: 518⟧ every ~10 min; any regression is caught within one tick.

**Catalog snapshot (dated; recompute `find catalog/<type> -name '*.yaml' | wc -l`):** as of 2026-06-20 —
adapters 33 · personas 233 · processors 180 · harnesses 195 · rubrics 245 · tools 173 (**1,059 components**) ·
pipelines 420. **Honesty note:** this is a *seeded* component library, not 1,059 measured-lift-verified
components. The moat is the **governed engine + the measured-lift admission gate + the proofs**, not the raw
count. Lead the pitch with the engine; the catalog is the developer funnel and the upgrade-path substrate.

### 1.2 What is a *labeled seam* (contract built, real backend deferred behind a port)

Per the **CLOUD-DEFER-ONLY-AFTER-LOCAL-EQUIVALENT** discipline, every external dependency is a swappable
adapter behind a capability port with a **working local equivalent first**. Today the governed runtime is
**stdlib-only** (deterministic local vector + stub LLM + SQLite; zero third-party repos imported). Real
backends (Postgres/pgvector, Temporal, Docling, Graphiti, Langfuse, k8s, cloud functions, frontier models)
are **cataloged candidates** that light up by config — they are not yet wired against live credentials. This
is a *strength* to state plainly: the abstraction is proven locally, so the first real dependency cannot land
without a card + contract test + fallback.

### 1.3 The demo (the forcing function)

- **Offline, deterministic:** `PYTHONPATH=. python3 scripts/demo_offline_full_baltor.py --self-test` — every
  core section fires; the CFPB correctness invariant holds.
- **Live dashboards:** the admin server (`:9301`) serves `/dashboard`, `/fleet` (live supervisor + the new
  execution-backend panels), `/consume`, projection-only over the durable stores.
- **Runs with no Redis, no pip, no cloud, no network LLM** — then scales to cloud by flipping policy/config.

---

## 2 · External cloud/web services, custom API endpoints & cloud functions (the toolkit)

This is the section the engine was built to earn. Baltor's core architectural bet: **the customer's task
contract is stable; the infrastructure under it is interchangeable.** Two layers deliver this.

### 2.1 Execution backends are interchangeable (run anything as a function, a pod, or a job)

`src/baltor/ports/execution_provider.py` defines one `ExecutionProviderPort`. A `CapabilityTask` is submitted
once; the **selector** (`execution_backend_selector.py`) chooses *where it runs* from:

```
local_subprocess · local_function_emulator · k8s_deployment_worker · k8s_job
aws_lambda · gcp_cloud_run_function · azure_function · cloud_run_job · browser_pool · gpu_pool · sandbox_worker
```

- **Policy + pricebook driven, reversible:** choice is made from a JSON policy matrix + a **pricebook**
  (`architecture/execution_backend_pricebook.json`, *configuration not code*) + provider health + creds.
  Change the pricebook → the choice flips, no code change. **Kubernetes and cloud functions run side by side**
  and can be turned on/off as pricing/latency/cold-start/customer-residency requirements change.
- **Cloud-deferred-never-blocking:** an unconfigured cloud backend falls back to the local executor; the
  capability still runs. *Cloud can wait; capability cannot.*
- **Hard guards:** browser / GPU / open-ended / control-plane work is excluded from generic cloud functions by
  default (cold-start + dependency weight) — overridable only with explicit proof.
- **Wired live + visible:** `supervisor_watch.step(execution_backend=True)` routes owned-shard work through the
  selector, records a switchable `ExecutionProviderDecision`, and the choice is visible on
  `/api/fleet/execution` + the `/fleet` page. Proof: `check_live_fleet_execution_backend_wiring`.

**For YC:** this is the literal answer to "can you run customer functions in the cloud, switch providers as
prices move, and stay multi-cloud?" — yes, and it's already wired and proven locally, so cloud is a config
flip, not a re-architecture.

### 2.2 Every external tool is a swappable adapter behind a capability slot

`architecture/external_capability_catalog.json` holds **30 capability slots**. Baltor domain code depends on a
`capability_slot`, never a vendor. Each slot carries a currently-wired adapter (a working stdlib stub today),
a candidate external primary, and fallbacks. Directly relevant to "custom API endpoints + cloud functions in
the toolkit":

| Slot | Today (active/candidate) | First real primary | Why it matters |
|---|---|---|---|
| `api_manager` | `apigw.stub@v1` | Portkey / LiteLLM / Kong | route **custom API endpoints** + LLM calls, cheapest-first, budgeted |
| `mcp_gateway` | `mcpgw.stub@v1` | IBM ContextForge / Docker MCP | expose **MCP servers/tools** as governed components |
| `api_catalog` | `apicat.stub@v1` | Apicurio | register + version customer endpoint schemas |
| `parser_manager` | `parser.stub@v1` | Docling → Unstructured | document parsing as a swappable backend |
| `scraping_manager` | `scrape.stub@v1` | Scrapy | source acquisition |
| `hybrid_retrieval` | **`vector.deterministic_local@v1` (active)** | pgvector / Qdrant | retrieval substrate, swappable |
| `durable_workflow_engine` | **`durable.sqlite_store@v1` (active)** | Temporal / DBOS | durable orchestration |
| `graph_db_substrate` / `temporal_graph_provider` | local stubs | FalkorDB / Graphiti | relationship + temporal facts |
| `observability_provider` / `eval_harness` | local trace / flywheel (active) | Langfuse / Phoenix | telemetry + evals |
| `sandboxed_execution` | `sandbox.worktree_nonet@v1` | E2B / microsandbox | run untrusted code/agents safely |
| `memory_provider` | `memory.baltor_local@v1` | Supermemory / Mem0 / Letta | memory as **candidate context, never truth** |
| `research_agent` | `research.local_stub@v1` | OWL / Browser-use / Skyvern | bounded agents that PROPOSE evidence |

Status enum: `active · candidate · experimental · deprecated · quarantined · replaced · foil · reference`.
Flagged-not-to-adopt-as-runtime (`foil`/quarantined): generic agent runtimes, archived/unverified tools.

**Product framing of "custom endpoints + cloud functions in our toolkit":** a customer (or OHH developer)
registers their own API endpoint or cloud function as an **Action** (the seven-primitive component grammar:
Input · Knowledge Corpus · If Statement · Action · Loop · Stop · Output) behind these same ports. It then
inherits governance for free — provenance, receipts, the measured-lift gate, the execution-backend selector,
and the cost meter. The toolkit is *bring-your-own endpoint/function, governed*.

---

## 3 · Horizontal & vertical scalability (the "fully working scalable demo" plan)

### 3.1 Horizontal scale (more throughput)

- **Stateless workers, durable ledger:** workers own a task only via an **atomic claim** — the SQLite analog
  today, Postgres `FOR UPDATE SKIP LOCKED` in production (same contract). Add workers → linear throughput; no
  duplicate processing.
- **Lightweight always-on control plane; expensive workers scale-to-zero.** The supervisor (leader + shard
  leases, CAS, generation/failover) coordinates many `--watch` processes against one ledger. Workers spin up
  on queue depth and drain to zero. The control plane itself scales as a replicated leader + shards with DB
  leases + idempotent decisions.
- **Backend elasticity:** the execution selector lets a lane burst onto k8s/KEDA or Cloud Run Jobs (Argo for
  large bounded DAGs) and fall back to local — *side by side*, switchable by policy. (Cost lanes already
  enumerated in `baltor-cloud-cost-pricing-pro-forma.md` §Worker Compute.)
- **Multi-cloud / residency:** because backend choice is policy, a tenant can pin AWS-only, GCP-only, or
  no-external-functions — without changing the task contract.

### 3.2 Vertical scale (more fidelity per fact)

- **Fidelity tiers** (⟦DECISION⟧ on the public tier *names* — see §6 consolidation): the same fact can be
  served at deterministic-only fidelity (cheap, fast) up through multi-source-corroborated + frontier-verified
  + human-confirmed (expensive, audit-grade). The verification rail + the cost meter make fidelity a dial.
- **Deeper governance per tenant:** per-tenant isolation, ACL-before-model, signed publishers, CDC/revocation
  on volatile facts, rehydratable old versions.
- **Substrate depth:** identity/claims/lineage/receipts → Postgres (object + long tables + JSONB); big
  artifacts → object store; embeddings → vector index; relationships → temporal graph. Text files stay
  docs/schemas/fixtures only.

### 3.3 Demo maturity ladder (what to show, in order)

1. **Now:** offline deterministic full demo + live `/dashboard` + `/fleet` (local, $0).
2. **Design-partner staging:** managed Postgres + queue + object store + small worker pool + one authority
   feed; before/after report. ($250–$1.5k/mo.)
3. **Burst proof:** flip one lane to KEDA/Cloud Run, show the same run scale horizontally and the
   execution-backend panel reflect the switch — *the multi-cloud, switchable story made visible*.

---

## 4 · Business plan (consolidated from the authoritative pricing doc)

> Source of truth: `docs/strategy/baltor-cloud-cost-pricing-pro-forma.md`. Refresh competitor/pricing links
> before any quote or deck.

### 4.1 Economic unit & meters (do NOT price by seat)

`source monitored → facts verified → context package served → downstream agent risk reduced.`
Meters: monitored sources · documents/pages processed · facts under management · verification jobs · served
context packages · premium public context feeds · frontier-model overage.

### 4.2 Pricing tiers (⟦DECISION⟧ — ranges are drafts pending owner sign-off)

| Tier | Target | Included |
|---|---:|---|
| Design-partner pilot | $5k–$25k fixed | 2–6 wks, 1 corpus, 1–2 authority feeds, before/after report |
| Team | $1.5k–$3k/mo | small source set, light verification, limited exports |
| Business | $6k–$15k/mo | scheduled sync, multi-source verification, package serving, audit exports |
| Enterprise | $40k+/yr (often $75k–$250k ACV) | private deploy, SSO, custom connectors, source policies, SLAs |

### 4.3 Open-core monetization boundary (the join)

- **Free funnel (Open Harness Hub):** open spec/SDK/engine; a **freezable** verified snapshot pulled into an
  OHH harness is free.
- **Paid (Baltor):** **live, kept-fresh** serving against a dynamic corpus; governed corpora subscriptions
  (Corpus); build-on-demand for a domain we don't yet carry (the **capability-request** is the demand-capture
  object). Consumption-shaped billing matches the SNOW/MDB tape.

### 4.4 Margins & pro forma (planning assumptions, not forecasts)

- Gross margin: pilots 40–60% (services + frontier heavy) → repeatable hosted 70–80% → public feeds highest.
- COGS rule (the moat as a cost lever): *every expensive bounded-agent discovery must distill into a cheaper
  deterministic rule/connector/parser* (Determinism Factory). Model/search/browser spend kept <10–20% of
  recurring revenue.
- ARR scenarios — Conservative / Base / Upside: M12 $180k/$350k/$750k · M24 $750k/$1.8M/$4.0M ·
  M36 $1.8M/$5.0M/$12.0M.

### 4.5 TAM / market (⟦DECISION⟧ — comparable-anchored, label as estimate in the deck)

Position in the **consumption-priced "context layer"** the public tape just validated: SNOW (product rev
$1.33B/qtr, +34%), MDB ($687.6M, +25%), DDOG (+32%), NET (+34% on agentic). The named winners sell
*infrastructure*; OSS memory/RAG frameworks give *plumbing*; **both lack enterprise governance — glossary,
lineage, entity resolution.** Baltor/OHH is the **open, governed assembler at that seam**. We do not out-RAG
incumbents; we **wrap** them (Qdrant/Mem0/LLMLingua/Langfuse) as governed, measured-lift components under one
provenance/eval contract. Bottom-up wedge first (regulated-context buyers), expand along the consumption axis.

---

## 5 · The YC pitch deck (slide-by-slide)

> Render to slides as-is. Keep claims to what the proofs support (assurance brand — overclaiming is fatal).

1. **Title** — *AI Done Right · Baltor.ai.* "Models don't fail. Their context does." [founder, contact]
2. **Problem** — Enterprise agents fail because their context is **stale, contradictory, unverified, and not
   packaged for consumption**. Today teams paper over it with manual review that doesn't scale and no audit
   trail. (Buyer pains: "our agents cite stale policy"; "our documents disagree"; "we don't know which facts
   are safe to serve.")
3. **Why now** — Every augmented AI workflow needs trustworthy data underneath it; the context layer is being
   repriced by consumption (SNOW/MDB/NET). Frontier models keep improving — which makes *context*, not raw
   capability, the durable bottleneck and the durable moat.
4. **Solution** — Baltor: a **governed Context Engine**. Sync → version → reconcile → verify → reconcile-
   conflicts → keep-fresh → compress → serve, with **lineage + a portable receipt on everything**. Pillars:
   Verified · Current · Efficient · Provable.
5. **Demo** — the CFPB correctness invariant, live: Reg-E "10 business days" served; the 30-day FAQ and the
   narrative allegation **held out**; only the reconciled winner served, with its source authority and a
   receipt. Then OFAC: the connector deterministically flags a HELD-OUT would-be sanctions violation (an always-green synthetic conformance test, plus a dated 2026-06-14 `--live` catch against the real SDN list). *Runs offline, deterministically.*
6. **Product / how it works** — the six stages + verification rail; agents **PROPOSE**, Baltor **DISPOSES**;
   memory/LLM/browser output is candidate context, never truth; the promotion boundary (candidate ≠ served).
7. **Moat** — **Verified + Current + Provable + cost-efficient governed DATA** + the **Determinism Factory**
   (expensive resolution becomes cheap deterministic infrastructure over time, losslessly) + portable
   receipts + measured fidelity. Not "capability the next model can't reach."
8. **The toolkit / platform** — bring-your-own **API endpoints and cloud functions**, governed; 30 swappable
   capability slots; multi-cloud + k8s/serverless **side by side, switchable by policy**; scale-to-zero.
9. **Market** — the consumption context layer; open governed assembler at the governance seam; wrap, don't
   replace, the infra incumbents. (TAM estimate, comparable-anchored — ⟦DECISION⟧.)
10. **Business model** — usage meters (not seats); open-core (free freezable snapshot / paid live layer);
    pilot → Team → Business → Enterprise; build-on-demand + Corpus subscriptions.
11. **GTM** — beachhead where context change = legal/financial risk (sanctions, export controls, vendor
    compliance, regulated procurement, legal ops). Founder-led outbound + OHH open-source developer funnel +
    design-partner pilots. Hook: *"We find the stale and weak facts your agent would otherwise cite."*
12. **Competition** — 2×2 / table: enterprise search (Glean), RAG platforms (Contextual AI — absorbed into
    Google DeepMind May 2026), vector DBs, knowledge graphs, GRC tools, source intelligence. Baltor's column:
    *verify + package + prove facts before agents use them; lifecycle-managed fact state with history.*
13. **Traction / milestones** — *be honest:* a working governed engine (⟦computed: 518⟧ deterministic proofs, full offline
    demo, OFAC: an always-green synthetic conformance proof AND a dated 2026-06-14 `--live` catch on the real SDN list) + locked brand + owned domains. Seed-readiness gates: 3 design partners, 1 paid
    pilot, 1 exported package consumed by a real downstream agent/RAG stack, measured stale-fact catch + manual-
    review reduction.
14. **Team** — technical founder; training-free / frozen-model + legal-AI background (favors structural,
    deterministic, governance-first methods — exactly this product's grain). [fill in.]
15. **The ask** — ⟦DECISION⟧ raise size + use of funds: connectors/source monitoring · worker
    orchestration · verified public context feeds · local+cloud deployment hardening · security/compliance
    baseline · design-partner success + founder-led GTM. (YC-stage: typically a pre-seed/seed round — set the
    exact figure with the owner.)

---

## 6 · Opportunities for consolidation (the real cleanup backlog)

These are inconsistencies/sprawl found while writing this doc. Each is a warranted change; none should be made
unilaterally on brand/strategy — confirm with owner, then supersede the stale artifact in the **same** change.

1. **Retire "Gold context" / Bronze-Silver-Gold medallion as the headline tier.** Owner direction is explicit:
   "gold doesn't mean anything." `baltor-gtm-fundraising-plan.md` and `baltor-medallion-context-positioning.md`
   still lead with "Gold context." Replace the *headline* with explicit **fidelity tiers** (Verified ·
   Provable); medallion may stay only as an industry *reference* to Databricks' model, never our product noun.
   (Repo code/proofs are already 100% free of "golden" as of 2026-06-06.)
2. **Reconcile bounded-agent naming.** "Hermes / OpenClaw" (in the GTM + pricing docs) predates the canonical
   **ContextOps Verification Foundry** (bounded agents that PROPOSE) + **Determinism Factory** (distillation).
   Pick the canonical terms repo-wide; supersede the old code names.
3. **Collapse the "two services" language into the locked brand.** CEaaS / "Context Enrichment service" /
   "verified-context SaaS" = **Baltor.ai**. Code paths (`services/products/context_enrichment/`, `oh_ce` CLI,
   `web/context-enrichment/`) still carry the old name — a tracked rename, already noted in
   `brand-architecture.md`.
4. **De-duplicate the strategy-doc sprawl.** There are many overlapping docs (gtm-fundraising-plan,
   gtm-launch-guide, gtm-onepager, pricing pro-forma, several competitive-* docs, acquihire/acquisition). Make
   **this doc the index/master** and demote the rest to depth-references; merge the 3–4 competitive docs into
   one.
5. **Make "what counts as a real component" unambiguous.** 1,059 catalog entries vs measured-lift-verified
   components — publish the distinction (the two-axis lift gate is the admission rule) so the deck never
   implies 1,059 proven components.
6. **Capability catalog → real adapters behind the CLOUD-DEFER discipline.** 30 slots are mostly stdlib stubs;
   the consolidation is to land each first real adapter *only after* a local equivalent + contract test +
   fallback exist (mirror the execution-backend work just shipped).

---

## 7 · Risks & mitigations

| Risk | Mitigation |
|---|---|
| **Data-gravity incumbents** (Snowflake/Databricks add governance) | be the *agent-neutral, open, governed assembler at the seam*; wrap their substrate, don't compete on storage; portable receipts travel across platforms |
| **Frontier models close the "capability gap"** | moat is **governed DATA + provenance + freshness + receipts**, not capability; the lift gate is an internal selection criterion, not the external story |
| **No traction yet** | lead with the working engine + the design-partner gates; the asset is the proof, not the logo wall |
| **Services-heavy early margin** | Determinism Factory turns each expensive resolution into reusable cheap infrastructure; COGS discipline in the pricing doc |
| **Over-broad surface (1,059 components, 30 slots)** | the engine is the product; the catalog is the funnel; the lift gate keeps the catalog honest |
| **Regulated-domain liability** | assurance brand discipline — never claim "100% accurate"; review queues, signed publishers, held-out unverified facts, audit trail |

---

## 8 · 90-day plan to YC-ready

1. **Land 3 design partners** in the sanctions/vendor-compliance beachhead with real corpora.
2. **One paid pilot** that **exports a package consumed by the customer's own agent/RAG stack** — the single
   most important external proof point.
3. **Quantify** stale/weak-context caught + manual-review reduction (the before/after report becomes the deck's
   traction slide).
4. **Burst demo**: flip one worker lane to a real cloud backend (Cloud Run Job or KEDA) on staging and show the
   execution-backend panel reflect the live switch — proves the multi-cloud/scalable story end-to-end.
5. **Execute the §6 consolidation** so the deck, docs, and code tell one consistent story.
6. **Owner decisions:** finalize pricing numbers, the raise size + use-of-funds, and the public fidelity-tier
   names; clear the BALTOR trademark + grab the remaining domains.

---

*Warrant: written on clear owner intent (this request). Grounded in the LOCKED brand
(`brand-architecture.md`), the authoritative pricing pro forma, the PMF/TAM doc, the live execution-backend
work (⟦computed: 518⟧ green proofs as of 2026-06-20), and the capability catalog. Pricing, raise size, TAM math, and
public tier names are flagged ⟦DECISION⟧ and must not be treated as decided. No brand/strategy decision was
made unilaterally; §6 lists the supersessions to confirm with the owner.*
