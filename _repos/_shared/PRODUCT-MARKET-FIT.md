# Product–Market Fit — consolidated thesis

> **What this file is.** A single lossless consolidation of the product–market-fit
> thesis for the portfolio (AI Done Right → Teleon → Baltor → OpenHubForAI). It
> summarizes and links to the detailed strategy documents; it invents no facts.
> The single operational **entry-point goal** is [`codex/master-goal.md`](codex/master-goal.md) (the
> long-horizon program an agent executes); this doc is its product–market-fit companion.
> **Path convention:** short-form citations resolve to the canonical multi-repo layout — `docs/`,
> `scripts/`, `architecture/` live under `_repos/shared-backend-components/`; `src/teleon/…` under
> `_repos/teleon/backend/`; `src/baltor/…` under `_repos/baltor/backend/`. The
> reconciling source when documents disagree is
> [`docs/strategy/portfolio-pmf-solidification-2026-07-01.md`](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md),
> which explicitly names every claim it supersedes. Every claim below cites its source
> path. Each section marks **PROVEN** (a dated artifact or implemented code exists) vs
> **THESIS** (a stated hypothesis not yet demonstrated).

---

## 1. The wedge — primitives are the core product; AIDevObserver leads go-to-market

**The center of gravity is the primitive substrate.** Teleon, AIDevObserver, and Baltor
are all *consumers* of the primitives; the substrate itself is the product. The bar the
substrate must clear: organized, searchable, small, short, remixable — such that a coding
agent completes real tasks by reading only the **edges** of primitives
(`input_edge`/`output_edge` contracts, blackbox one-liners), never full code, and orders
them into a graph runtime. Source:
[`portfolio-pmf-solidification-2026-07-01.md` §1](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md).

**AIDevObserver leads the public story** (the wedge goes first). The lead message is
developer speed through reuse — *"Stop AI coding agents from rebuilding what your team
already has"* — with safety/compliance as a secondary lens, never the lead. Teleon is the
engine (mostly hidden); OpenHubForAI is the registry source (shown only in matches); Baltor
is the verified context layer (deferred). First buyer: AI-platform / DevEx /
engineering-productivity lead. Source:
[`portfolio-pmf-solidification-2026-07-01.md` §2](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md).
This resolves the older contradiction where separate docs led with different products.

- **PROVEN (infrastructure):** substrate state verified 2026-07-01 — 72,804 edge cards,
  5,005 search cards, 41 primitive-kind families, 200 runtime shapes, 193 source-backed
  groups with proof bundles; edge-aware lexical search is live
  (`src/teleon/observer/registry_search.py`); the DAG executor is real
  (`src/teleon/dag/pipeline_dag.py`). AIDevObserver: 16/16 screens live, 14 intervention
  modules, consent gate built. Source:
  [`portfolio-pmf-solidification-2026-07-01.md` §1, §4](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md).
- **THESIS (evidence):** "the open gap is EVIDENCE, not infrastructure." No benchmark yet
  isolates primitive lift (bare agent vs primitive-first agent), and every record remains
  `candidate`/`serves_truth=false` — the promotion gate has never been crossed. Source:
  [`portfolio-pmf-solidification-2026-07-01.md` §1, §6](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md).

## 2. The moat stack — governed data > lift bar > determinism factory

The strategy documents carried competing moat framings; the reconciled hierarchy (per the
owner reframe) is three layers, ranked. Source:
[`portfolio-pmf-solidification-2026-07-01.md` §3](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md).

1. **External moat (what we sell): governed data** — Verified, Current, Provable context
   with provenance, freshness/CDC, and receipts. Orthogonal to model progress. This is the
   external pitch. Sources:
   [`north-stars.md` §4](../shared-backend-components/docs/strategy/north-stars.md),
   [`first-live-capability-sanctions-screening.md` §7](../shared-backend-components/docs/strategy/first-live-capability-sanctions-screening.md).
2. **Internal bar (what we admit): the two-axis lift gate** — lift over the bare model AND
   structural durability (`scripts/eval/reason_codes.py`). A *selection criterion*, not the
   pitch. See §4 below.
3. **Supporting engine (how it compounds): the Determinism Factory + reuse flywheel** —
   expensive resolution distilled losslessly into deterministic rules from *verified* cases;
   accepted/dismissed findings become team memory. This makes the data moat cheaper to
   maintain; it is not itself the lead claim. Source:
   [`portfolio-pmf-solidification-2026-07-01.md` §3](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md).

The earlier documents are now read as layers under this lead: the Baltor GTM plan's
procedure-mining moat and the monetization brief's lift-gate moat are layers 3 and 2 beneath
the governed-data lead. Sources:
[`baltor-gtm-fundraising-plan.md` "Moat"](../fundraising/context/baltor-gtm-fundraising-plan.md),
[`product-market-monetization-brief.md` "The moat"](../shared-backend-components/docs/strategy/product-market-monetization-brief.md).

- **PROVEN:** a governed `serves_truth=true` output exists end-to-end — the OFAC SDN
  screening verdict, a deterministic computation over a signed authoritative source carrying
  a portable receipt (list version + content hash + match lineage). A dated `--live` catch
  on 2026-06-14 fetched the production SDN list (content hash `e30f6077…`, 19,065-row source)
  and held a planted synthetic bad claim out of the served corpus; receipt
  `docs/strategy/evidence/ofac-live-run-2026-06-14.json`. Source:
  [`first-live-capability-sanctions-screening.md` §4](../shared-backend-components/docs/strategy/first-live-capability-sanctions-screening.md).
- **PROVEN:** the moat is against retrieval-only incumbents — enterprise search, RAG
  platforms, vector DBs, and knowledge graphs return a stale/contradictory fact with high
  similarity and zero provenance because verification is not their job; we wrap, not replace
  them. Source:
  [`first-live-capability-sanctions-screening.md` §7](../shared-backend-components/docs/strategy/first-live-capability-sanctions-screening.md).
- **THESIS:** the reuse/experience-database flywheel ("which compositions work, at what cost,
  with which model") compounding into millions of traces is a stated moat, not yet
  demonstrated at scale. Source:
  [`product-market-monetization-brief.md` "The moat" layer 3](../shared-backend-components/docs/strategy/product-market-monetization-brief.md).

## 3. Total addressable market — the consumption-priced context layer

**THESIS (market read).** The market the public tape validated in 2026 is a
**consumption-priced context layer**: AI feeds the data platform more work — retrieval,
memory, real-time signals, governance — billed per query / per GB / per inference. The named
public-market prints cited (Snowflake product revenue $1.33B +34%, MongoDB $687.6M +25% with
Atlas +29%, Datadog +32%, Cloudflare +34%) share this story. The winners sell *infrastructure*
and the open-source memory/RAG frameworks give the *plumbing*; **both leave the same gap** —
enterprise governance (glossary, lineage, entity resolution). That seam is OpenHubForAI: the
open, governed *assembler* of the context layer — wrapping the infra (Qdrant/Mem0/LLMLingua)
as governed, measured-lift components under one provenance/eval contract. Source:
[`context-layer-pmf.md`](../shared-backend-components/docs/strategy/context-layer-pmf.md).

The billing axes are already consumption-shaped — build-on-demand (per assembled flow),
live_subscription (per governed-corpus refresh), hosted_endpoint (per metered retrieval call)
— matching the per-query / per-GB / per-inference motion, applied to the *governed component
layer* rather than raw storage. Source:
[`context-layer-pmf.md` "Why the model fits"](../shared-backend-components/docs/strategy/context-layer-pmf.md),
[`monetization-mechanisms.md`](../shared-backend-components/docs/strategy/monetization-mechanisms.md).

The 7-layer context stack maps onto the taxonomy; the two open **build gaps** are memory and
caching (plus graph-RAG and MCP connectors). Source:
[`context-layer-pmf.md` "The 7-layer context stack"](../shared-backend-components/docs/strategy/context-layer-pmf.md).

## 4. The admission bar — two-axis: lift AND durability

A component earns a place only if **(a)** it lifts (`pipeline_score − bare_model_score > 0`
on a real task) AND **(b)** the lift is **structural** — it won't close when the next model
ships. Transient lift (a fact a bigger model absorbs, a tool you could wire) is revenue today
but depreciating inventory, never a defensibility claim. Build where the advantage is
structural: a body, a login, a license, accountability, a deterministic verifier, or a
volatile/un-ingestible source. The taxonomy (lift_reason → durability_class, mechanisms,
retrievability tiers, decay_signal) has a single source in code: `scripts/eval/reason_codes.py`;
the sorter is `scripts/eval/durable_gap_harness.py` — never re-defined in prose. Sources:
[`north-stars.md` §2](../shared-backend-components/docs/strategy/north-stars.md),
[`capability-valleys.md`](../shared-backend-components/docs/concepts/capability-valleys.md),
[`product-market-monetization-brief.md` "Positioning"](../shared-backend-components/docs/strategy/product-market-monetization-brief.md).

The one question: *will this gap close on its own?* Transient gaps discount to no moat;
durable gaps are where the human advantage is not a text-prediction advantage at all, or the
authoritative source lives in a channel a pipeline structurally cannot ingest. Source:
[`capability-valleys.md` "The one question"](../shared-backend-components/docs/concepts/capability-valleys.md).

Supporting discipline: **screen before you collect** — a cheap Stage-1 gap screen weighted
toward model-independent signals, then an expensive Stage-2 confirm on a thin sample, scaling
only confirmed gaps (`scripts/acquisition/gap_screen.py`). Source:
[`north-stars.md` §1, §3](../shared-backend-components/docs/strategy/north-stars.md).

- **PROVEN:** the gate culls filler — it already removed ~1,980 padded candidates. Source:
  [`product-market-monetization-brief.md` "Risks"](../shared-backend-components/docs/strategy/product-market-monetization-brief.md).
- **PROVEN:** a measured freshness/lift delta exists — on a 2026 regulatory change (measured
  2026-05-28 via Ollama), the bare model answered the stale value (PHP 500k) and the grounded
  pipeline answered correctly (PHP 1M): a measured +1.0 lift. Source:
  [`monetization-mechanisms.md`](../shared-backend-components/docs/strategy/monetization-mechanisms.md).
- **THESIS:** the systematic primitive-lift A/B (bare coding agent vs primitive-first agent,
  scored on correctness/proof/tokens/time) is the missing instrumentation, not yet run.
  Source:
  [`portfolio-pmf-solidification-2026-07-01.md` §6](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md).

## 5. Target verticals — regulated-fact; avoid insurance; healthcare-administration starter

**Where the lift is largest and most provable: compliance / risk / audit teams in regulated,
esoteric domains** (sanctions/AML, export controls, vendor compliance, supply-chain due
diligence, regulated procurement, legal/policy operations, ESG/CSDDD, GxP, customs & trade).
They pay, and they need exactly what is uniquely offered — proof, citations, provenance,
review trails, signed facts, revocation — not "ask the model." Sources:
[`product-market-monetization-brief.md` "the wedge"](../shared-backend-components/docs/strategy/product-market-monetization-brief.md),
[`baltor-gtm-fundraising-plan.md` "Beachhead"](../fundraising/context/baltor-gtm-fundraising-plan.md).

**The named ICP:** the person personally accountable when a wrong fact reaches a regulator,
auditor, or customer — Head of Compliance, BSA/AML Officer, Sanctions Compliance Lead, Legal
Ops, GRC owner — *not* the person buying a faster model. Trigger / why-now: the EU AI Act and
peers make "the model decided" non-compliant; frontier models make context the durable
bottleneck; the context layer is being repriced by consumption. Source:
[`first-live-capability-sanctions-screening.md` §1–§3](../shared-backend-components/docs/strategy/first-live-capability-sanctions-screening.md).

**Scope rail (LOCKED): avoid insurance.** Do not build or expand insurance pipelines; target
the claims-*shape* in adjacent regulated verticals instead; synthetic/public data only, no
real PII. Enforced by `scripts/check_adjacent_verticals.py`. Sources:
[`decisions-locked-2026.md` row A10](../shared-backend-components/docs/strategy/decisions-locked-2026.md),
`CLAUDE.md` "Safety And Scope".

**Starter vertical (depth before breadth): healthcare-administration provider-directory
data** — administrative directory fields only (name, NPI, specialty, practice, address,
phone, website, status). Explicitly **excludes insurance and clinical/PHI data**;
synthetic/public metadata only. The design-partner *target* (not a closed customer;
pre-revenue) is HealthLynked. The concrete first win is provider-directory accuracy +
freshness: NPI Luhn validation, normalization, NPI-exact + bounded fuzzy match, cross-source
agreement confidence, and a decision boundary (high-confidence agreed change → auto-update;
conflict/low-confidence → human review; no unsafe write). Code:
`src/teleon/verticals/provider_directory.py`, `provider_sources.py`. Source:
[`first-live-capability-sanctions-screening.md` §5, §6](../shared-backend-components/docs/strategy/first-live-capability-sanctions-screening.md).

- **PROVEN:** the first live capability (OFAC SDN screening) and the provider-directory
  modules are implemented, with a dated offline demo and proof gate (recompute
  `PYTHONPATH=. python3 scripts/run_proofs.py`). Source:
  [`first-live-capability-sanctions-screening.md` §4–§6](../shared-backend-components/docs/strategy/first-live-capability-sanctions-screening.md).
- **THESIS:** the vertical is **pre-revenue, design-partner stage** — the asset is a working
  governed engine with the moat mechanics built in, *not traction*. No signed design partner
  yet; no customers/logos claimed. The before/after pilot metrics (stale facts caught,
  manual-review reduction, cost-per-1,000 records, freshness lag) are the pilot's metrics, not
  results. Sources:
  [`first-live-capability-sanctions-screening.md` §5, §6](../shared-backend-components/docs/strategy/first-live-capability-sanctions-screening.md),
  [`portfolio-pmf-solidification-2026-07-01.md` §4](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md).

## 6. Monetization — open-core: exports are the free funnel, the governed live layer is the revenue

**The line:** open the protocol + engine, commercialize the governed content + live service.
The export is the commodity — a user who describes a task, gets a blueprint, and self-hosts it
should be able to leave for free; that is the funnel, not the business. Recurring revenue is
**everything an export can't freeze**. Sources:
[`open-core-model.md`](../shared-backend-components/docs/strategy/open-core-model.md),
[`monetization-mechanisms.md`](../shared-backend-components/docs/strategy/monetization-mechanisms.md),
[`product-market-monetization-brief.md` "Build-on-demand"](../shared-backend-components/docs/strategy/product-market-monetization-brief.md).

**OPEN (free funnel, MIT/CC-BY):** the protocol/spec (seven-primitive model, schemas,
component/ID/hash format), the engine (validator, foundry pipeline code, CLI), the
logic/gate/design-system, externally published/verified public knowledge (gov agencies,
standards bodies), and two top-precedence carve-outs — **public-good** components
(anti-trafficking, child-safety, humanitarian, free even as RAG/runtime) and **anything a
government entity publishes via a verified account**.

**COMMERCIAL (subscription/metered):** the verified RAG databases / curated corpora, custom
tools, runtime-heavy functions, **dynamic corpora** (freshness/CDC/revocation), and hosted
execution of code-executing components. Source:
[`open-core-model.md` "The line"](../shared-backend-components/docs/strategy/open-core-model.md).

The boundary aligns with the execution-class model: `static-information` + `text-operation`
components are freezable (free); `code-executing` + dynamic-corpus are live (recurring). Two
orthogonal billing axes are **implemented and stamped on each `index_record`** —
**openness** (`open`/`commercial`, `scripts/foundry/openness.py`) and **delivery**
(`frozen_export` / `live_subscription` / `credentialed_data` / `hosted_endpoint`,
`scripts/foundry/access.py`). Source:
[`monetization-mechanisms.md` "Two orthogonal axes"](../shared-backend-components/docs/strategy/monetization-mechanisms.md).

**Sequenced revenue.** First dollar (the wedge): Pro/Team subscriptions for a private
registry + task-to-costed-blueprint, plus paid managed ingestion. Expansion: usage metering,
private tenant registries, verified-publisher accounts, marketplace revenue share, API access.
Enterprise: BYO-cloud/VPC/air-gapped packages, audit/compliance packs, custom benchmarks.
Illustrative price anchors (validate against real runs): Free $0 · Pro ~$29–49/seat/mo · Team
~$199–499/mo · Enterprise custom. Source:
[`product-market-monetization-brief.md` "Monetization Channels", "Pricing"](../shared-backend-components/docs/strategy/product-market-monetization-brief.md).
The full 20-mechanism catalog (freshness SLA tiers, alerting/webhooks, bulk corpus/data
licensing to AI labs, measurement-dataset licensing, eval-as-a-service, white-label/OEM) is in
[`monetization-mechanisms.md`](../shared-backend-components/docs/strategy/monetization-mechanisms.md).

Baltor's own model mirrors this: recurring source monitoring, metered verification/refresh,
hosted serving packages, premium verified public context feeds, enterprise/on-prem. Source:
[`baltor-gtm-fundraising-plan.md` "Business model"](../fundraising/context/baltor-gtm-fundraising-plan.md).

- **PROVEN:** the openness + delivery classifiers are implemented and stamped on
  `index_record` (`scripts/foundry/openness.py`, `access.py`); from one EU source the foundry
  routes the verified RAG corpus → commercial and the public-regulation grep rules → open.
  Source:
  [`open-core-model.md` "How the foundry routes"](../shared-backend-components/docs/strategy/open-core-model.md).
- **THESIS / not yet built:** actual billing is a deliberate `NotConfigured` stub
  (`scripts/billing_plane.py` StripeAdapter — owner-gated, never faked); no production
  domains/DNS/TLS; AIDevObserver not yet packaged (no PyPI/marketplace/MCP-directory). These
  three are "the whole distance between built and sellable." Pricing anchors are illustrative,
  not validated. Sources:
  [`portfolio-pmf-solidification-2026-07-01.md` §4](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md),
  [`product-market-monetization-brief.md` "Pricing"](../shared-backend-components/docs/strategy/product-market-monetization-brief.md).

## 7. Proven vs thesis — the honest ledger

| Claim | Status | Source |
|---|---|---|
| Substrate built (72,804 edge cards, 41 kind families, 200 runtime shapes; DAG executor real; edge search live) | **PROVEN** (dated 2026-07-01) | [pmf-solidification §1](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md) |
| One governed `serves_truth=true` output end-to-end (OFAC verdict, receipted) | **PROVEN** (dated 2026-06-14 `--live`) | [sanctions §4](../shared-backend-components/docs/strategy/first-live-capability-sanctions-screening.md) |
| Measured freshness lift (+1.0, bare vs grounded on a regulatory change) | **PROVEN** (2026-05-28 via Ollama) | [monetization-mechanisms](../shared-backend-components/docs/strategy/monetization-mechanisms.md) |
| Edge-first context reduction (M0: 486x at output equivalence, +8 MB/+0.6 s tax) | **PROVEN** (dated 2026-07-01, deterministic floor) | [pmf-solidification §6](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md) |
| Lift gate culls filler (~1,980 padded candidates removed) | **PROVEN** | [monetization brief "Risks"](../shared-backend-components/docs/strategy/product-market-monetization-brief.md) |
| Openness + delivery billing axes classified and stamped | **PROVEN** (implemented) | [open-core](../shared-backend-components/docs/strategy/open-core-model.md), [monetization-mechanisms](../shared-backend-components/docs/strategy/monetization-mechanisms.md) |
| Systematic primitive-lift A/B (bare vs primitive-first agent) | **THESIS** (not yet run) | [pmf-solidification §1, §6](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md) |
| Every record still `candidate`/`serves_truth=false` (promotion gate never crossed, except OFAC) | **THESIS / open gap** | [pmf-solidification §1](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md) |
| Signed design partner / recurring revenue | **THESIS** (pre-revenue) | [sanctions §5](../shared-backend-components/docs/strategy/first-live-capability-sanctions-screening.md), [pmf-solidification §4](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md) |
| Billing live; production domains; AIDevObserver packaged | **THESIS / not built** (the 3 revenue blockers) | [pmf-solidification §4](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md) |
| Consumption-context-layer TAM read; acquisition angle | **THESIS** (market read) | [context-layer-pmf](../shared-backend-components/docs/strategy/context-layer-pmf.md) |
| Reuse/experience-database flywheel compounding at scale | **THESIS** | [monetization brief "The moat"](../shared-backend-components/docs/strategy/product-market-monetization-brief.md) |

## Sources (detailed docs — read these for depth)

- [`docs/strategy/portfolio-pmf-solidification-2026-07-01.md`](../shared-backend-components/docs/strategy/portfolio-pmf-solidification-2026-07-01.md) — the reconciling PMF synthesis (wedge, moat hierarchy, product verdicts, evidence program). Authoritative on conflicts.
- [`docs/strategy/context-layer-pmf.md`](../shared-backend-components/docs/strategy/context-layer-pmf.md) — consumption context-layer TAM, the 7-layer stack map, acquisition read.
- [`docs/strategy/north-stars.md`](../shared-backend-components/docs/strategy/north-stars.md) — negative-space corpus, two-axis admission, screen-before-collect, governance-is-the-product, maintenance > acquisition.
- [`docs/strategy/teleon-baltor-openhubforai-portfolio.md`](../shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md) — canonical brand + dependency architecture (Baltor → Teleon → OpenHubForAI, enforced).
- [`docs/strategy/product-market-monetization-brief.md`](../shared-backend-components/docs/strategy/product-market-monetization-brief.md) — problem, product, ICP, wedge, differentiation, competitive landscape, moat, pricing/packaging, MVP.
- [`docs/strategy/baltor-gtm-fundraising-plan.md`](../fundraising/context/baltor-gtm-fundraising-plan.md) — Baltor positioning, beachhead, buyer, pilot offer, fundraising narrative, seed milestones.
- [`docs/strategy/open-core-model.md`](../shared-backend-components/docs/strategy/open-core-model.md) — the open/closed product line and how the foundry routes each side.
- [`docs/strategy/monetization-mechanisms.md`](../shared-backend-components/docs/strategy/monetization-mechanisms.md) — the two billing axes and the full 20-mechanism catalog.
- [`docs/strategy/first-live-capability-sanctions-screening.md`](../shared-backend-components/docs/strategy/first-live-capability-sanctions-screening.md) — named ICP, acute pain, first live capability (OFAC), healthcare-admin starter vertical, why-incumbents-can't.
- [`docs/concepts/capability-valleys.md`](../shared-backend-components/docs/concepts/capability-valleys.md) — the theory of defensible (durable) gaps; taxonomy single-sourced in `scripts/eval/reason_codes.py`.
- [`docs/strategy/decisions-locked-2026.md`](../shared-backend-components/docs/strategy/decisions-locked-2026.md) — locked scope rails including A10 (avoid insurance).

*Consolidation warrant: add-only file under `context/`, grounded in the strategy docs cited
above; no facts invented, no numbers fabricated (each metric cites the doc it comes from);
PROVEN vs THESIS marked throughout. Where documents conflicted, the 2026-07-01 PMF
solidification synthesis governs.*
