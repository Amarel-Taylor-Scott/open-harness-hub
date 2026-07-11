# Acquihire Roadmap — turning Open Harness Hub into a fully working, acquirable startup

> **Audience & purpose.** A concrete, repo-grounded plan to take Open Harness Hub
> from "engine + catalog + implemented front-end" to a **demoable, billable
> product** positioned as an **acquihire** for Meta Superintelligence Labs,
> GitHub/Microsoft, OpenAI, Anthropic, and Google. This is an execution doc, not a
> pitch: every claim points at a file. It sits beside
> `docs/strategy/acquisition-positioning.md` (the *why a lab buys us* brief) and
> turns it into a *what we build, in what order, and what we lead each acquirer
> with*.
>
> **Honesty rule.** Throughout, "implemented" means a module with a passing
> self-test or a committed artifact; "designed" means a spec doc with no running
> code; "gap" means neither. The same discipline the product enforces
> (`docs/codex/master-goal.md`: report *useful-promoted*, never *generated*) applies
> to this roadmap's own status claims.

---

## 1. The thesis (one paragraph)

Open Harness Hub is the **operating layer for what models still can't do
reliably**: a database-backed registry of AI-pipeline components whose *only*
admission rule is **measured capability lift over a bare LLM** that is also
**structurally durable** — it won't close when the next model ships
(`docs/codex/master-goal.md` "usefulness bar"; `docs/strategy/north-stars.md` §2
two-axis admission; `scripts/eval/reason_codes.py` is the single source of the
durability taxonomy). Most AI apps decay as models improve; this one *compounds*,
because the lift gate prunes anything a better model absorbs and re-parks the
catalog on the moving frontier, while the **governance moat** — provenance, signed
facts, citations, review trails, freshness/CDC/revocation — is orthogonal to model
quality and is exactly what regulated buyers pay for
(`docs/strategy/acquisition-positioning.md` "anti-fragile to model progress";
`docs/strategy/north-stars.md` §4 governance-is-the-product). The components are
produced by the **foundry** — 22 self-tested modules (`scripts/foundry/`) that mint
a component *only* with three pillars of evidence (a measured gap, a real licensed
source, a measured lift), so filler is impossible by construction
(`docs/architecture/evidence-driven-component-factory.md`;
`python -m scripts.foundry.pipeline --self-test` passes today). And the bar is not
our assertion: **SkillsBench / Skill Lift** (BenchFlow, Kaggle May–Jul 2026) is the
field's third-party, peer-reviewed measurement of *exactly* our admission criterion
— per-skill lift, public→private generalisation, an adversarial safety gate — and we
already export every catalog Action to a submittable `SKILL.md` bundle and import
its tasks as evidence triples (`docs/strategy/skillsbench-alignment.md`;
`scripts/foundry/skillsbench.py` self-test passes).

---

## 2. "Fully working startup" — gap analysis (exists vs missing)

The legend below is used in every row. **Status is honest** — a design doc is not a
running system.

| Status | Meaning |
|---|---|
| ✅ **Built** | committed + a passing self-test or rendered artifact |
| 🟡 **Partial** | core runs, but a load-bearing piece is missing |
| 🟠 **Designed** | spec doc exists, no running code |
| 🔴 **Gap** | neither — must be built for "fully working" |

### 2.1 Cloud infrastructure (Render → K8s)

| Piece | Status | Evidence / what's missing |
|---|---|---|
| Topology decision (4 tiers: request / async worker / scheduled / data) | ✅ Built (design) | `docs/architecture/cloud-architecture.md` — *queue + worker tier non-negotiable; K8s earned, not day-one*. |
| Foundry shaped for queue/worker (stages, partitions, resumable ledger, `run_fleet` fan-out) | ✅ Built | `scripts/foundry/` (`worker.py`, `queues.py`, partition/ledger design); per-job `model_call_budget` is the cost gate. |
| pgvector bootstrap (local) | ✅ Built | `infra/postgres/docker-compose.pgvector.yml`; dim/model single-sourced in `scripts/_config.py` (`DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"`, dim 384, via `pgvector_type()`). |
| Phase-1 deploy (Cloudflare/CDN → web/API → managed queue → workers → Neon pgvector → R2) | 🟠 Designed | Topology mapped (`cloud-architecture.md` Phase 1, ~$40–90/mo) but **not stood up** in a cloud account. |
| Phase-2 K8s (KEDA scale-on-queue-depth, Helm + Terraform, BYO-cloud / air-gap) | 🟠 Designed | Phase 2 specified; *the acquisition lever* (a lab runs the whole stack in their infra) — build only when scale/enterprise pulls. |
| Hosted-endpoint model proxy (metered) | 🟡 Partial | `scripts/foundry/model_route.py` is the proxy + scraper/measurement caller; **not yet a metered request-tier service**. |

**Net:** the *substrate is queue-ready by design* (the hard part) and pgvector is
bootstrapped locally; the **gap is a real cloud deployment** of Phase 1.

### 2.2 Billing / metering (Stripe + credits)

| Piece | Status | Evidence / what's missing |
|---|---|---|
| Billable-event model (the *what to meter*) | ✅ Built | `scripts/foundry/access.py` — 4 delivery modes (`frozen_export` · `live_subscription` · `credentialed_data` · `hosted_endpoint`) × 3 events (`refresh` · `data_query` · `hosted_call`); self-tested; stamped on each `index_record`. |
| Openness classification (free vs commercial, per component) | ✅ Built | `scripts/foundry/openness.py` (public-good carve-out → verified-authority → execution → provenance precedence). |
| 20 monetization mechanisms catalogued | ✅ Built (design) | `docs/strategy/monetization-mechanisms.md` (tiers, freshness SLA, audit packs, measurement-dataset licensing #19). |
| **Stripe integration** (subscriptions, usage records, webhooks) | 🔴 Gap | Front-end has `/checkout`/`/upgrade`/`PCheckout` (`web/design/HANDOFF.md` §2); **no payment processor wired**. |
| **Credits ledger** (build-on-demand spend, community-build earn) | 🔴 Gap | Designed (`monetization-mechanisms.md` #6); `web/design/HANDOFF.md` §10 lists "metering→billing (Stripe) + credits ledger" as an *engineering workstream, not yet built*. |
| Metering→billing bridge (worker emits event → meter → invoice) | 🔴 Gap | `access.py` *defines* the events; nothing accumulates them into a billable counter yet. |

**Net:** the **economic model is fully specified and the per-component billing axes
are implemented**; the **gap is the plumbing** — Stripe + a credits ledger + a
meter-at-the-worker bridge.

### 2.3 Auth / tenancy

| Piece | Status | Evidence / what's missing |
|---|---|---|
| Auth UI (signin/signup/onboarding) | ✅ Built (front-end) | `web/pages/auth.js`; `PSignin`/`POnboarding` in the handoff route map. |
| Roles UI | ✅ Built (front-end) | `/roles` → `PRoles` (`web/design/HANDOFF.md` §2). |
| **Identity provider** (real auth: sessions, OAuth/SSO) | 🔴 Gap | UI only; no backend identity. `HANDOFF.md` §11: "SSO·SCIM provisioning" still **unbuilt**. |
| **Tenant isolation** (per-tenant data boundary, private registries) | 🔴 Gap | Listed as an engineering workstream (`HANDOFF.md` §10 "tenant isolation"); private-tenant-registry is mechanism #13 but unimplemented. |
| Per-tenant concurrency / anti-scrape lever | 🟠 Designed | `HANDOFF.md` §10: priority queue with per-tenant concurrency = the anti-scrape lever; foundry `queues.py` is the seam. |

**Net:** **front-end complete, backend identity + multi-tenancy is a gap.** This is
the single biggest "fully working SaaS" gap after billing.

### 2.4 The live governed layer (CDC freshness + revocation + signing / C2PA)

| Piece | Status | Evidence / what's missing |
|---|---|---|
| Freshness model (dated snapshot vs maintained feed) | ✅ Built (design+code seam) | `access.py` `live_subscription`/`refresh`; `monetization-mechanisms.md` "freshness engine". |
| Scrapers as a first-class source surface (date + provenance + source_url) | 🟡 Partial | `scripts/foundry/scrapers.py` + `sources.py` (`SourceScout`); the gov-scraper pattern is specified, breadth of live feeds is thin. |
| **Measured freshness lift** (the proof) | ✅ Built (one instance) | `monetization-mechanisms.md`: a 2026 regulatory change — bare model said stale **PHP 500k**, grounded pipeline said correct **PHP 1M** → **measured +1.0 lift** (live, via Ollama). This is the canonical "what an export can't freeze" proof. |
| CDC / revocation propagation to subscribers | 🟠 Designed | `docs/architecture/component-cdc-versioning.md`, `promotion-cdc-bridge-plan.md`; not running as a live feed with alerts. |
| **Signing / C2PA** (signed attestation of a flow + cited facts) | 🟡 Partial | C2PA **emitter** exists (`scripts/emit/c2pa.py`) + front-end `/attest`/`PAttest`; **key/signing infra + canary registry** is an unbuilt workstream (`HANDOFF.md` §10). |
| Governance emitter surface (provenance coverage) | ✅ Built | 13 emitters incl. `c2pa.py`, `spdx_3.py`, `eu_ai_act_annex_iv.py`, `cyclonedx_ml.py`, `openlineage.py` — the standards-crosswalk the regulated wedge needs (`north-stars.md` §4). |

**Net:** the **moat's mechanics are implemented at the emitter/billing-axis layer
and proven once (+1.0)**; the **gap is operating it live** — running scrapers on a
cadence, propagating CDC/revocation, and standing up signing-key infra.

### 2.5 SOC2 / GDPR

| Piece | Status | Evidence / what's missing |
|---|---|---|
| Data hygiene posture (no real PII/secrets; public/synthetic only) | ✅ Built (policy) | `CLAUDE.md` "Safety And Scope"; `north-stars.md` safety stance; `_reference/` never republished. |
| Provenance/license spine (per-row source_url + license + author) | ✅ Built | Master-goal gate #5; foundry stamps provenance; SPDX/EU-AI-Act emitters feed Art. 11 evidence. |
| Audit/review trail (review tickets, replayable `PipelineObject`) | ✅ Built | `review_ticket` row family; `cloud-architecture.md` "the `PipelineObject` is a replayable audit record". |
| **SOC2 Type II** (controls, evidence, audit) | 🔴 Gap | `HANDOFF.md` §10 lists "SOC2/GDPR" as an unbuilt workstream — no controls program, no auditor. |
| **GDPR/DPA** (legal pages, DPA, data-subject flows) | 🔴 Gap | `HANDOFF.md` §11: legal pages (terms / privacy / **DPA**) still route to 404. |

**Net:** **strong technical pre-conditions** (provenance, audit trail, no-PII
policy) but **no compliance program**. SOC2/GDPR are table-stakes for the
regulated-vertical wedge buyer and a diligence checklist item for an acquirer — but
they are *process*, not engineering, and can run in parallel.

### 2.6 The front-end (now implemented from the design handoff)

| Piece | Status | Evidence |
|---|---|---|
| Design system (Scheme S · Harness House; 9 schemes × light/dark; token contract) | ✅ Built | `web/styles/oh-tokens.css`, `oh-components.css`, `oh-explorations.css`; ported verbatim from the handoff (`web/design/HANDOFF.md` §3). |
| Landing + logged-out preview funnel (modality tabs, example chips, hero A/B flag) | ✅ Built & wired | `web/index.html` + `web/app.js`; `PLanding`/`PPreview` call the **real** `/api/build`. |
| Build → flow → run, Explore (pipelines/components/detail), Foundry/Workers, Govern (`/freshness`,`/attest`,`/trust`,`/audit-log`), Connect (`/improve`,`/connect`,`/sources`), Account | 🟡 Partial | ~40 routes specified with CSS present (`web/design/PAGES.md`, `HANDOFF.md` §2); landing+preview live, the rest **specced & ready to port** (one `<div data-route>` + nav entry each). |
| Served behind the showcase server with a public token-gated URL | ✅ Built | `scripts/showcase/server.py` serves `web/` + real `/api/build|export|components|primitives`; live URL in `dist/showcase-share-url.txt`. |
| Designed states (empty / loading / **blocked-by-gate** / error / simulate / zero-result→capability-request) | ✅ Built | `oh-explorations.css` + `HANDOFF.md` §6 — *the blocked-by-gate state visibly shows "unproven lift / unsourced provenance" — the moat, rendered.* |

**Net:** **the front-end is implemented and demoable** (landing + preview wired to a
real backend over 2,400+ indexed components); the gap is *porting the remaining
~40 specced routes*, which is mechanical (CSS already present).

### 2.7 The data flywheel (the durable, compounding asset)

| Piece | Status | Evidence / what's missing |
|---|---|---|
| Foundry end-to-end (gap → source → construct → standardize → novelty → measure → gate → stage_load) | ✅ Built | `scripts/foundry/` 22 modules; `--self-test` passes incl. *"anti-filler: every promoted row is fully evidenced"*. |
| Lift gate with a **hard floor** (cull what doesn't lift) | ✅ Built | `dist/reports/capability-lift-gate.json`: `lift_floor: 0.2`, **kept 2,397 / culled 1,980** of 4,377 (the filler the gate rejects). |
| Demand graph (capability-requests → prioritized build queue) | 🟡 Partial | `scripts/foundry/interactions.py` + front-end `/requests`/`PRequests`; the privacy-redacted **interaction→demand** loop is designed (`acquisition-positioning.md` asset #5), not yet fed by live traffic. |
| **Real embeddings loaded** (hybrid keyword+vector+graph search) | 🔴 **Gap (the #1 blocker)** | README computed stats: **0 embeddings** in `dist/catalog.sqlite`. Master-goal **gate #6** (vectorization) and **P1 exit** both block on this. `stage_load` flags embeddings as *placeholder* today. |
| Measurement dataset (`bare_vs_pipeline` deltas at scale — acquisition asset #1) | 🟡 Partial | The mechanism exists (`scripts/foundry/measure.py`); one canonical measured instance (+1.0). The **scarce, model-improving signal** is real but **thin** — depth is the flywheel's job. |

**Net:** the **flywheel's machinery is built and self-tested**; it is **not yet
spinning at volume** — the two things that make it spin are **real embeddings**
(unblocks hybrid search + promotion gate #6) and **live traffic** (feeds the demand
graph + grows the measurement dataset).

### 2.8 Gap summary — the critical path to "fully working & billable"

Ordered by leverage (each unblocks the next):

1. 🔴 **Real embeddings** → unblocks hybrid search, promotion gate #6, and the
   product's whole retrieval premise (P1 exit). *Cheapest, highest leverage.*
2. 🔴 **Stripe + credits ledger + meter-at-worker** → turns the implemented billing
   *axes* into actual *revenue*.
3. 🔴 **Backend auth + tenant isolation** → turns the auth *UI* into a real SaaS.
4. 🟡 **Phase-1 cloud deploy** (Render/Cloud Run + queue + Neon pgvector + R2) →
   the substrate the above three run on.
5. 🟡 **Live governed layer** (scraper cadence + CDC/revocation + C2PA signing
   keys) → operates the moat, not just emits it.
6. 🟡 **Port the remaining front-end routes** (mechanical; CSS present).
7. 🔴 **SOC2/GDPR program** (process, parallel track) → wedge-buyer table stakes.

---

## 3. The 90-day plan (week-by-week themes)

Three 30-day arcs. Each arc has a single headline outcome. The plan obeys the
master-goal phase order (`docs/codex/master-goal.md`): **don't scale before the
foundation holds** — P1 (foundation) before P4 (sellable) before P5 (volume).
Honest accounting per the daily contract: report the **funnel**
(`probed → confirmed → sourced → built → novel → measured → promoted`), never
"generated".

### Arc A (Weeks 1–4) — **Foundation: make retrieval & the loop real**
*Headline outcome: hybrid search returns the catalog with real vectors; the foundry
loop runs on a cloud worker; one wedge family has a re-confirmed measured lift.*

- **W1 — Embeddings.** Wire real embeddings in `stage_load` (Stage 7) using
  `all-MiniLM-L6-v2` (dim 384, `scripts/_config.py`) or a hosted route; embed the
  committed components; load `object_embedding`; run `vector_readiness_audit.py`.
  *Exit: README stats show non-zero embeddings; gate #6 can pass.*
- **W2 — Hybrid search + promotion gate.** Stand up keyword+vector+graph+facet
  search over the embedded catalog; make `capability_lift_gate` *gate* (hard floor
  0.2), not just score (master-goal gate #4). *Exit: search returns real components;
  promotion blocked without a real vector.*
- **W3 — Phase-1 cloud deploy.** Stand up `cloud-architecture.md` Phase 1: web/API
  (Render/Cloud Run) + managed queue + a worker running `Foundry.run_partition` +
  Neon pgvector + R2. One container, two start commands. *Exit: the foundry runs a
  partition on a cloud worker behind a queue.*
- **W4 — Re-prove one wedge lift, live.** Re-run the measurement loop on the ESG /
  CSDDD family (we already have the assets + the +1.0 freshness instance) to produce
  a fresh `bare_vs_pipeline` delta with provenance. *Exit: a current, dated measured
  lift on the demo path.*

### Arc B (Weeks 5–8) — **Billable: auth, metering, the governed layer**
*Headline outcome: a logged-in user can run a build, hit a metered governed query,
and be billed; freshness/CDC operates on at least one live corpus.*

- **W5 — Backend auth + tenancy.** Real identity (sessions/OAuth), tenant boundary,
  private-registry scoping. Wire the existing auth UI (`web/pages/auth.js`) to it.
  *Exit: real login; per-tenant data isolation.*
- **W6 — Stripe + credits.** Subscriptions + usage records + webhooks; a credits
  ledger for build-on-demand. Wire `/checkout`/`/upgrade`. *Exit: a test card buys
  Pro; a metered event appears on an invoice.*
- **W7 — Meter-at-worker bridge.** Accumulate `access.py` events (`refresh` /
  `data_query` / `hosted_call`) at the worker into billable counters; enforce
  per-job budgets + per-tenant concurrency (the anti-scrape lever). *Exit: usage =
  revenue, runaway cost capped.*
- **W8 — Live governed layer (one corpus).** Run a gov scraper on a cron
  (`scrapers.py`) capturing date+provenance+source_url; wire CDC/revocation to fire
  an alert when a cited fact changes; stand up C2PA signing keys so `/attest` emits a
  *signed* attestation. *Exit: one corpus is live-fresh; a changed fact propagates;
  an attestation is cryptographically signed.*

### Arc C (Weeks 9–12) — **Demoable & defensible: front-end, flywheel, the case**
*Headline outcome: the full headline interaction (paste→costed→governed→deployable
flow) works end-to-end on the live site, the flywheel is spinning, and the
acquisition artifacts are assembled.*

- **W9 — Port the core product routes.** Build/Flow/Run, Explore
  (`/pipelines`,`/components`,`/c/:slug`), Foundry/Workers from `web/design/PAGES.md`
  (CSS present; mechanical). *Exit: paste-to-flow works on the live URL, not just
  the classic UI.*
- **W10 — Port the Govern + Connect surfaces.** `/freshness`, `/attest`, `/trust`,
  `/audit-log`, `/improve` (Import & Improve), `/connect` (MCP), `/sources`. *Exit:
  the moat is visible in-product; Import & Improve runs a measured before/after.*
- **W11 — Spin the flywheel.** Feed privacy-redacted live interactions into the
  demand graph (`interactions.py`); run the daily gated loop at a modest partitioned
  volume (10×1k design, not monolithic); grow the measurement dataset. *Exit: the
  funnel dashboard shows promoted/day > 0 with measured lift; demand→build has ≥1
  conversion.*
- **W12 — Assemble the case + submit SkillsBench.** Export the catalog's Actions to
  `SKILL.md` bundles (`scripts/foundry/skillsbench.py`) and **submit to Skill Lift**;
  freeze the metrics pack (§5); record the demo. Start the SOC2/GDPR program in
  parallel (legal pages, controls scoping). *Exit: a SkillsBench submission, a
  one-take demo video, and the metrics one-pager.*

> **If a path blocks, branch — don't stop** (`CLAUDE.md` "What To Do When Stuck";
> the `direction`/`goal` skills). If the cloud deploy stalls, port front-end routes
> or grow the measurement dataset; if a scraper source is blocked, switch source
> surfaces. The 90-day *outcomes* are fixed; the *order within an arc* flexes.

---

## 4. Per-acquirer fit thesis

Each row extends `docs/strategy/acquisition-positioning.md` "Why each acquirer
specifically" into **the one asset that matters most to them, the one demo to lead
with, and the one metric to put on the slide.** The five acquirable assets are
fixed (`acquisition-positioning.md` "The acquirable assets"): (1) the **measurement
dataset**, (2) the **governed fresh-fact flywheel**, (3) the **open standard +
community**, (4) the **foundry**, (5) the **demand graph**.

### Meta Superintelligence Labs
- **Why acquihire:** Meta's edge is *open weights + ecosystem distribution*. An open
  protocol/engine for describing, validating, running, and composing components — the
  canonical **index** others publish into — is distribution for the open-weights
  ecosystem (`acquisition-positioning.md`: Meta → "an open standard + community").
- **Asset that matters most:** **#3 the open standard + community** (the foundry and
  measurement dataset are the credibility behind it). The seven-primitive grammar +
  schemas + emitters are already MIT/CC-BY (`docs/strategy/open-core-model.md`).
- **Lead demo:** the **open author→validate→run→compose loop** end-to-end on open
  weights (the catalog already has Ollama/local-Gemma adapters) + the live front-end
  as the public Hub.
- **Lead metric:** **catalog breadth × open-tier coverage** — manifests indexed
  (computed README stat, 2,537 today) and the % classified `open` by
  `openness.py`; framed as "the registry the open ecosystem composes in."

### GitHub / Microsoft
- **Why acquihire:** the cleanest strategic fit — a **governed component registry
  adjacent to the dev workflow**, the "**Docker-Hub-for-pipelines**" framing with
  evals + costed deploys (`acquisition-positioning.md`: GitHub → that exact phrase;
  seeded by Hassan Gasim's framing, README "Notable integrations").
- **Asset that matters most:** **#3 the open standard** *plus* **#4 the foundry** as
  a registry+CI primitive — components with measured evals, SPDX/SBOM
  (`scripts/emit/spdx_3.py`, `cyclonedx_ml.py`), and one-click costed deploy bundles
  (Terraform/Helm, the Phase-2 enterprise asset).
- **Lead demo:** **paste a task → costed, deployable bundle**, then *export to a repo
  + CI* — the registry as a dev primitive; the C2PA/SPDX attestation as the
  supply-chain story Microsoft already sells.
- **Lead metric:** **costed-blueprint coverage + provenance coverage** — % of
  returned flows that are fully costed and carry SPDX + C2PA, i.e. shippable through
  a governed dev pipeline.

### OpenAI
- **Why acquihire:** a **registry + builder + marketplace layer above
  GPTs/Assistants**, with the experience DB + demand graph + **managed governance for
  enterprise** (`acquisition-positioning.md`: OpenAI row).
- **Asset that matters most:** **#5 the demand graph** + **#1 the measurement
  dataset** — a model-independent map of *what enterprises need next* and *where
  grounded pipelines beat bare models*, both directly steering product + post-training
  priorities.
- **Lead demo:** the **headline interaction** (paste→costed governed flow) as the
  marketplace/builder layer, plus the **blocked-by-gate state** (`HANDOFF.md` §6) —
  "the marketplace that refuses to ship a component that doesn't measurably help."
- **Lead metric:** **measured-lift distribution + demand→build conversion** —
  promoted-with-positive-Δ count and the rate at which unmet-need requests convert to
  built, governed components.

### Anthropic
- **Why acquihire:** the **most native fit to the house ethos** — a
  governance-/safety-native registry (human oversight, provenance, review gates),
  Claude as the builder/judge, and the "what models can't do reliably" discipline
  (`acquisition-positioning.md`: Anthropic row). The foundry's agents are *designed*
  to be Claude sub-agents (`evidence-driven-component-factory.md`: gap-prober /
  source-scout / component-author / lift-judge).
- **Asset that matters most:** **#1 the measurement dataset** *as a safety+capability
  signal* — and the **safety gate itself**. SkillsBench's ClawsBench (unsafe →
  −1.0) maps one-to-one onto our `gate.py` + review queues
  (`docs/strategy/skillsbench-alignment.md`); the lesson that *LLM-self-authored
  components are net-negative* is empirical backing for human-approval-by-design.
- **Lead demo:** the **foundry as a Track-2 meta-skill** — "a system that writes and
  refines other skills *under a budget* without producing unsafe ones"
  (`skillsbench-alignment.md` "Acquisition narrative"), with the human-approval queue
  on every knowledge component and Claude as gap-prober/judge.
- **Lead metric:** **lift *with* a passing safety gate** — promoted-with-positive-Δ
  *and* zero open high-risk review tickets; the SkillsBench Skill-Lift score as the
  external, peer-reviewed proof that the registry adds capability *without* a safety
  cost.

### Google
- **Why acquihire:** **enterprise governance + regulated-vertical PMF on top of
  Vertex / Agent Builder**, with **BYO-cloud / air-gap** fit
  (`acquisition-positioning.md`: Google row).
- **Asset that matters most:** **#2 the governed fresh-fact flywheel** + the
  **BYO-cloud/air-gap deployability** (Phase-2 Helm/Terraform,
  `cloud-architecture.md`) — exactly the regulated-enterprise governance story
  Vertex needs, deployable in the customer's VPC.
- **Lead demo:** the **+1.0 freshness lift** (`monetization-mechanisms.md`: stale
  PHP 500k → fresh PHP 1M) — a fact changes upstream, CDC propagates, the cited fact
  updates, the attestation re-signs; the whole stack running in a *self-hosted* /
  air-gapped config.
- **Lead metric:** **governance coverage + freshness SLA (CDC latency)** — % of
  facts sourced/verified/fresh and the time from upstream change → propagated
  revocation; the regulated-buyer's defensibility number.

> **Common thread:** to *every* acquirer, the pitch is identical and stated in
> `acquisition-positioning.md`: *"the better the model, the tighter we focus on what
> it still can't do."* The differentiator is *which acquirable asset* we put on the
> first slide.

---

## 5. The artifacts & metrics that make the case

The honest funnel is the operating dashboard (`acquisition-positioning.md` "Metrics
that matter"): **`probed → confirmed → sourced → built → novel → measured →
promoted`** — always **useful-promoted/day**, never "generated"
(`docs/codex/master-goal.md` "Daily contract"). The case is built from these
artifacts; the parenthetical is where each lives **today** so claims stay honest.

1. **Measured lift numbers.**
   - *Today:* the canonical **+1.0 freshness lift** (stale PHP 500k → fresh PHP 1M,
     live via Ollama; `docs/strategy/monetization-mechanisms.md`); the
     **capability-lift gate** report (`dist/reports/capability-lift-gate.json`:
     floor 0.2, kept 2,397 / culled 1,980 of 4,377 — the gate visibly rejecting
     filler).
   - *To build (Arc A/C):* the **measured-lift distribution** across the wedge
     families via `scripts/foundry/measure.py` — the *scarce, model-improving
     `bare_vs_pipeline` signal* (acquisition asset #1, licensable; monetization
     mechanism #19).

2. **Governed-corpus size + provenance coverage.**
   - *Today:* computed catalog stats (**2,537 manifests, 670 committed**; refreshed
     by `scripts/build_readme_stats.py --check` — no hand-typed counts); 13 emitters
     incl. C2PA / SPDX 3.0 / EU AI Act Annex IV for the standards crosswalk; the ESG
     vertical **live-tested** (`data/esg-grep-findings.json`).
   - *To build:* **% sourced / verified / fresh** as a single governance-coverage
     metric, and CDC latency (freshness SLA) once the live layer runs (Arc B/W8).

3. **The foundry throughput (the flywheel).**
   - *Today:* **22 self-tested modules** (`scripts/foundry/`); the full pipeline
     self-test passes including *"anti-filler: every promoted row is fully
     evidenced"* (`python -m scripts.foundry.pipeline --self-test`); the SkillsBench
     bridge self-test passes (`scripts/foundry/skillsbench.py`).
   - *To build:* the **funnel dashboard** with **promoted/day (gate-cleared)** at a
     partitioned volume (Arc C/W11) — reported as the funnel, never a flat
     "generated" number.

4. **The live demo URL.**
   - *Today:* the implemented front-end (`web/`, Scheme S) served by
     `scripts/showcase/server.py` over the real `/api/build` (2,400+ indexed
     components) behind a **token-gated public URL** (`dist/showcase-share-url.txt`,
     currently `https://updated-concepts-mathematical-programme.trycloudflare.com/?token=…`).
   - *To build:* the **full headline interaction live** (Arc C) + a one-take recording
     leading with the **blocked-by-gate** state (the moat, rendered).

5. **The SkillsBench submission.**
   - *Today:* the catalog is **submittable today** — `action_to_skill()` derives a
     genuine `SKILL.md` from each Action's real structure
     (`docs/strategy/skillsbench-alignment.md`); `task_to_evidence()` imports the 94
     public tasks as gold-tier (recorded-confirmation) evidence triples *without
     fabricating a Δ*.
   - *To build (Arc C/W12):* an **actual Skill Lift submission** — the external,
     peer-reviewed proof that turns "does this make models more capable, provably,
     without a safety cost?" from *our assertion* into *a third party's published
     metric*.

### The honest one-pager (what goes on the slide)

| Metric | Today (cited) | Target by Day 90 |
|---|---|---|
| Measured lift | +1.0 freshness instance; gate floor 0.2 culls 1,980/4,377 | a lift distribution across ≥3 wedge families |
| Catalog | 2,537 manifests / 670 committed *(computed)* | + **non-zero embeddings**, hybrid search live |
| Foundry | 22 modules, full self-test passes | promoted/day > 0 at partitioned volume (funnel) |
| Governance | 13 emitters (C2PA/SPDX/EU-AI-Act); ESG live-tested | governance-coverage % + CDC latency on ≥1 live corpus |
| Demo | landing+preview live on token-gated URL | full paste→costed→signed→deployable flow live |
| External proof | SkillsBench bridge self-tests pass | a Skill Lift **submission** |
| Billable | billing axes implemented (`access.py`) | a paid Pro subscription + a metered invoice |

---

## Reconciliation & grounding

This roadmap **executes** `docs/strategy/acquisition-positioning.md` (the *why*) and
is bounded by `docs/codex/master-goal.md` (phase order, the lift bar, the daily
funnel contract, the non-negotiables). It changes no strategy; if it ever conflicts
with `master-goal.md`, the master goal wins (`master-goal.md` Reconciliation map).

*Grounds: `docs/codex/master-goal.md`; `docs/strategy/{acquisition-positioning,
open-core-model,monetization-mechanisms,north-stars,skillsbench-alignment}.md`;
`docs/architecture/{cloud-architecture,evidence-driven-component-factory}.md`;
`README.md`; `CLAUDE.md`; `web/README.md` + `web/design/{HANDOFF,PAGES}.md`;
`scripts/foundry/` (22 modules, `pipeline.py`/`skillsbench.py` self-tests pass);
`scripts/foundry/{access,openness,measure,model_route}.py`; `scripts/_config.py`
(embedding dim/model single source); `scripts/emit/` (13 emitters);
`dist/reports/capability-lift-gate.json`; `data/esg-grep-findings.json`;
`dist/showcase-share-url.txt`; `infra/postgres/docker-compose.pgvector.yml`.*
