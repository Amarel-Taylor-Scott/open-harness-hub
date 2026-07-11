# Architecture for acquirers — the technical-asset brief (PRIVATE)

> **Audience.** Acquirer technical due diligence (eng/infra/security reviewers at a
> data-platform, hyperscaler, dev-platform, or model lab). This is the *system* view:
> what the codebase actually is, how it is laid out, what runs today, and what is
> specified-but-not-built. It is the architecture counterpart to the two business-side
> acquihire docs — [[../../strategy/acquisition-positioning.md]] (*why a lab buys us*) and
> [[../../strategy/acquihire-roadmap.md]] (*what we build, in what order, per acquirer*).
> It does **not** restate those; it grounds the assets they name in files and the service
> registry so a reviewer can verify every claim.
>
> **Warrant (per [[../../codex/change-verification-contract.md]]):** user-intent — the owner
> asked for *acquihire prep + full docs + dogfood + use cases*, and specifically for "the
> TECHNICAL-ASSET brief for acquirer due diligence." Grounded in established repo principles
> (the master goal, the seven-primitive grammar, no-magic-values, schema-extensibility) and
> in the service registry. **Honesty rule observed:** every count below is computed (cited to
> its source); `active` vs `planned` vs `aspirational` is marked throughout, using
> `services/registry.yaml`'s own `status` field as the source of truth. Generated/aspirational
> counts are never presented as shipped.

---

## 0. What is being acquired, in one paragraph

A **governed component network** for the AI context layer: a database-backed registry of
reusable pipeline components, expressed in a small **seven-primitive grammar**, produced by an
evidence-gated **foundry**, scored by a **measurement engine** (capability lift + tier
fidelity), and exposed through **two product surfaces over one shared backend** — Open Harness
Hub (build/monitor *bounded* governed pipelines) and Baltor / Baltor (a content +
corpus refinery that serves governed *fuel* into *open-ended* agents). The defensible asset is
not the volume of rows; it is the **architecture that makes a row trustworthy** — one
provenance trail, one lift+fidelity score, one set of standards emitters — and the fact that
the same governed object monetizes through *two* doors with *one* COGS. The substrate is
provider-neutral and **BYO-cloud / air-gap deployable**, which is both the enterprise tier and
an acquisition lever (a lab runs the whole stack in its own infra).

---

## 1. The macro shape — two products, one shared platform plane

The single most important architectural decision (owner, 2026-05-29,
[[../../strategy/two-services-shared-infrastructure.md]]): **two genuinely distinct products on
two domains, sharing the entire infrastructure plane** — clusters, workers, the engine, the
data plane, governance, tooling. *One COGS, two revenue lines.* This is explicitly **not** one
web app with a brand toggle — an earlier draft framed it that way and the owner reversed it; the
reversal is now a structural rule in the change-verification contract.

```
   builders ─▶ ┌────────────────────────┐   ┌────────────────────────────┐ ◀─ agent devs
               │ OPEN HARNESS HUB        │   │ CONTEXT ENRICHMENT (Baltor)  │  (Claude Code,
               │ bounded                 │   │ unbounded                   │   Cursor, any
               │ • assemble DAG·run/trace│   │ • ingest content/corpora    │   MCP client)
               │ • registry·I/O rules    │   │ • tier raw→compressed→      │
               │ • monitor + LIFT gate   │   │     hyper-efficient         │
               │ sells: governed PIPELINES│  │ • host / download · 4 surfaces│
               └───────────┬────────────┘   │ sells: governed FUEL         │
                           │   two doors,    └──────────────┬───────────────┘
                           ▼   one object                   ▼
                ┌──────────────────────  THE JOIN  ──────────────────────┐
                │ a governed Knowledge Corpus / Action — minted ONCE,     │
                │ one provenance trail, one lift + fidelity score.        │
                │ Wire it into a bounded pipeline, OR serve it to an open │
                │ agent. Every component is sellable through either door. │
                └───────────────────────────┬─────────────────────────────┘
                                             ▼
   ┌────────────────────────  SHARED PLATFORM PLANE  ───────────────────────┐
   │ ingestion · foundry · measurement · enrichment · retrieval · governance │
   │ compute (K8s · worker fleet · vLLM) · data (Postgres+pgvector · object  │
   │ store · Redis · event bus) · telemetry (OTel · Prometheus · JSON logs)  │
   └─────────────────────────────────────────────────────────────────────────┘
```

Why share the plane: the expensive parts — clusters, workers, corpora, the
compression/measurement engine, governance — are **identical cost centers** for both products.
Compressing a corpus for a Baltor user and compressing one inside an OHH pipeline run the *same*
components on the *same* workers against the *same* store. A feature built for one product
(a better compressor, a fresher corpus, a new Action) is **instantly available to the other** —
which is only true because the data plane is **attribute-level, not column-level**
([[../../codex/schema-extensibility.md]]): a facet added for Baltor is a `dimension-record` row
both products read, never a column one product's loader knows about. Column-level facets would
silently fork the backend; attribute-level storage is the mechanism that keeps it genuinely
shared.

**Topology model:** *2 product services × 1 shared platform × 4 tiers*
([[../../architecture/backend-services-and-platform.md]], [[../../architecture/cloud-architecture.md]]).
The two product services are **thin request-tier doors** (`OH_PRODUCT`-pinned, identical
backend); all heavy work is the shared platform, reached synchronously (read APIs) or
asynchronously (enqueue a job). The four tiers are **request / async-worker / scheduled / data**
— and the load-bearing rule is *never run tier-2 work in a tier-1 request handler*: scrapers,
generation, measurement, and embeddings are **jobs behind a queue**, not web requests.

---

## 2. The service topology — `services/registry.yaml` is the map

The single source of truth for the backend service map is **`services/registry.yaml`**. Code
lives in `scripts/` (libraries by concern); `services/` is the thin service layer that *owns*
those packages; `infra/` is the topology. The registry's own `status` field is the honest line
between shipped and planned: `active` = a real runnable entrypoint exists today; `planned` =
boundary defined, code lives in `scripts/`, no single service entrypoint yet (migrates
incrementally, non-breaking).

| Service | Tier | `status` (registry) | Owns (`scripts/`) | Role |
|---|---|---|---|---|
| **harness-hub** (product) | request | **active** | `showcase` | OHH door — build · monitor; enqueues→foundry, reads→retrieval |
| **baltor** (product) | request | **active** | `showcase` | Baltor door — same image, `OH_PRODUCT`-pinned; reads→retrieval/enrichment |
| **ingestion** | async | **active** | `ingest`, `acquisition` | connectors · source registry · normalization; emits `source.normalized` |
| **foundry** | async | **active** | `foundry`, `factory` | gap→source→construct→measure→gate→load; scale-to-zero; emits `candidate.loaded` |
| **measurement** | async | **active** | `eval`, `verification` | lift harness + tier-fidelity; called by foundry **and** enrichment |
| **enrichment** (Baltor) | async | **planned** | `processors/{compression,memory,cache,retrieval}` | tier pipeline (raw→compressed→hyper-efficient); components seeded, tier entrypoint TBD |
| **retrieval** | request | **active** | `db`, `processors/retrieval` | vector/lexical/hybrid/graph query over pgvector |
| **governance** | scheduled | **active** | `db`, `_publish` | promotion readiness · CDC · provenance · signing; emits `promotion.ready`, `cdc.changed` |

Plus infra rows: a **worker** tier (`RedisQueue` default, Celery/Argo adapters opt-in) and a
**scheduler** tier (cron default, Airflow-Composer / Argo Workflows adapters). Datastores:
`postgres_pgvector` (operational + vector store), `object_store` (raw + tiered artifacts, R2/S3),
`redis` (broker + cache), `event_bus` (CDC / freshness / promotion pub-sub).

**Containerization:** *one image, per-service role* — the web/API tier and every worker are the
**same Docker image** started with a different command (commands live in the registry); the two
product services differ only by `OH_PRODUCT`. One build, one image to audit.

**Communication contract:** no shared mutable state between services. Sync read APIs for
low-latency lookups; everything bursty/long/cost-gated is an **idempotent job** on the `Queue`
protocol (`scripts/foundry/queues.py`); CDC/freshness/decay/promotion fan out as **events** on
the bus. Idempotency is structural: foundry stages are content-hashed and the funnel ledger is
resumable, so a retried or duplicated job converges (no double-promotion).

> **Migration honesty.** Today most `services/` entrypoints are thin wrappers over `scripts/`,
> so the documented fast-path keeps working; logic migrates folder-by-folder behind the
> boundaries over time. The boundaries, comms, and topology are *defined* now; the code moves
> behind them without breaking callers. A reviewer should read the registry as the contract and
> `scripts/` as the current implementation.

---

## 3. The grammar — seven primitives (the format-layer asset)

Everything in a pipeline reduces to **seven primitives**, all extending one generic shell
(`scripts/primitives/base.py::Primitive`, contract `run(po) -> po`). Canonical reference:
[[../../concepts/component-taxonomy-and-stages.md]]. This is the **format-layer moat** — the
thing an ecosystem composes in, analogous to what a container manifest or an SBOM format is to
its ecosystem.

1. **Input** — the payload to work on.
2. **Knowledge Corpus** — a store of facts, queried by a trigger (keyword / regex / rag_vector /
   exact_id / classifier / graph; static or dynamic).
3. **Conditional** (the IF) — the condition, kept separate from the THEN.
4. **Action** (the THEN) — anything that *does* something: a persona, tool, processor, harness
   (model call), adapter (model transport), rubric, or benchmark.
5. **Loop** — control flow / iteration.
6. **Stop / End** — halt early on a guard.
7. **Output** — finalize result + trace.

Each catalog `type` (the 14 storage keys) is a subtype of exactly one primitive; the folder
structure mirrors this (one file per primitive under `scripts/primitives/`), and **product
labels are derived** (`label_for_type` / `stage_for_type`) — there are no magic-string label
tables elsewhere. Two architectural consequences a reviewer should note:

- **Execution-class orthogonality.** Every component is exactly one of three execution classes
  — *static-information* (read-only), *text-operation* (pure transform), *code-executing* (runs
  code / calls an API / invokes a model). Only the third needs sandboxing, credentials, rate
  limits, and cost gates. This is what makes the security and cost story tractable: the boundary
  is *typed*, not ad hoc.
- **The capability-request is a typed empty slot, not an eighth primitive.** Unmet needs are
  captured as `capability-request` objects (`schemas/capability-request.schema.json`) carrying a
  `target_type` and lifecycle `abstract` — *never* tenant-visible as a component. This keeps
  "what role" (the seven primitives) and "how mature" (the lifecycle ladder) as two orthogonal
  axes, and it is the demand-capture object the business model monetizes (build-on-demand).

**The runtime contract** is one `PipelineObject` (`scripts/pipeline_object.py`) threaded through
every component — input, a shared mutable variable scope, a per-step `StepLog` (stage, exec
class, model-call flag, tokens, cost, timing, status), accumulated cost/tokens, outputs, errors.
It is JSON-round-trippable, so **a finished run is a complete, replayable audit record** — the
substrate for tracing, recommendation, and the governance trail.

---

## 4. The foundry — gap → source → construct → measure → gate → load

The components are produced by the **foundry** (`scripts/foundry/`, **21 modules** excluding
`__init__`; orchestrator `scripts/foundry/pipeline.py`). It is the durable, compounding asset:
a row is minted **only** with three pillars of evidence — a *measured gap*, a *real licensed
source*, and a *measured lift* — so filler is impossible by construction. The reported metric is
**promoted** (gate-cleared), never "generated."

The orchestrator (`Foundry.run_partition`) threads **eight stages**, recording the funnel after
each:

```
gaps_confirmed → sources_found → drafts_built → standardized → novel
              → lift_measured → promoted        (+ stage_load emits row families)
```

| Stage | Module | What it enforces |
|---|---|---|
| **gaps** | `gaps.py` | a measured capability gap exists (weak gaps rejected here) |
| **sources** | `sources.py` | a real licensed source with provenance (date + `source_url` + license) |
| **construct** | `construction.py` | build the component draft from the source |
| **standardize** | `standardize.py` | conform to the schema + seven-primitive grammar |
| **novelty** | `novelty.py` | reject near-duplicates / same-source clones |
| **measure** | `measure.py` | a measured `bare_vs_pipeline` lift (the measurement engine) |
| **gate** | `gate.py` | hard lift floor **+** durability **+** safety/human-approval routing |
| **stage_load** | `stage_load.py` | emit the row families; embeddings flagged **placeholder** pre-vectorization |

**Verifiable today:** `python3 -m scripts.foundry.pipeline --self-test` passes end-to-end
(offline). The self-test confirms the load-bearing behaviors a reviewer cares about: weak gaps
rejected at `gaps`, clones rejected at `novelty`, no-lift candidates culled at `gate`, a
promoted Knowledge Corpus **and** a Conditional each satisfying all three evidence pillars,
knowledge components minted at lifecycle `experimental` and held `pending human approval` while a
public-registry Conditional auto-approves, `object_embedding` flagged **placeholder** (the honest
pre-vectorization state), and the closing assertion *"anti-filler: every promoted row is fully
evidenced."* The fleet aggregates promoted across partitions — the affordable path to volume is
**partitioned fan-out** (one partition = one source vein = one worker), not a monolithic run.

**The cost gate is first-class.** Every async job carries a per-job `model_call_budget`
(`FoundryConfig`), which maps directly onto the queue's per-job budget; measurement model calls
are cost-gated; runaway cost is capped at the worker. This is the same seam the billing meter
uses (§7).

**Honest status of the flywheel.** The machinery is built and self-tested; it is **not yet
spinning at production volume**, and the gating blocker is real embeddings (§6). The
[[../../strategy/acquihire-roadmap.md]] gap analysis (§2.7) is the authoritative status ledger;
this doc does not restate it.

---

## 5. The measurement engine — lift + fidelity (the moat the model can't supply)

One engine, two questions — and it is shared by both products. The registry encodes this
directly: the **measurement** service is `called_by: [foundry, enrichment]`.

**(a) Capability lift — "does the pipeline lift over a bare model?"** The admission rule is
two-axis ([[../../codex/master-goal.md]], north-stars): a component is admitted **iff** it lifts
(`pipeline_score − bare_model_score > 0` on a real held-out task) **and** the lift is
**structural** — it won't close when the next model ships. The durability taxonomy is a **single
source of truth**: `scripts/eval/reason_codes.py` defines the enums (`DURABILITY_CLASSES`,
`DECAY_SIGNALS`, `MECHANISMS`, `RETRIEVABILITY_TIERS`, `LIFT_REASONS` → `durability_class`) and
must never be re-defined elsewhere; the sorter is `scripts/eval/durable_gap_harness.py`. The one
question that decides whether to build: *will this lift survive the next model?* — transient lift
(closes with scale/data/tools) is revenue-today-but-depreciating; structural lift (the advantage
isn't text-prediction at all — a body, a login, a license, accountability, a volatile source) is
the moat.

This bar is **externally validated, not self-asserted:** SkillsBench / Skill Lift (BenchFlow,
Kaggle 2026) measures *exactly* our criterion — per-skill lift, public→private generalization, an
adversarial safety gate — and the catalog already exports each Action to a submittable
`SKILL.md` and imports its tasks as evidence (`scripts/foundry/skillsbench.py`,
[[../../strategy/skillsbench-alignment.md]]).

**(b) Tier fidelity — "did the compressed tier preserve enough?"** The same engine extends to
Baltor: every tiered artifact ships a **published quality delta** (raw → compressed →
hyper-efficient) from a separate evaluator, never self-graded. The component exists in-catalog as
`catalog/processors/verify/compression-fidelity-check.yaml`. This is the load-bearing point for a
reviewer: **Baltor adds no new measurement engine** — it is the OHH lift gate, re-pointed from
"does the pipeline lift?" to "did the tier preserve?". One moat, sold through two doors.

**Verifiable artifact today:** the capability-lift gate report
(`dist/reports/capability-lift-gate.json`) records `lift_floor: 0.2` and, run across the catalog,
**kept 2,397 / culled 1,980 of 4,377** — the gate visibly rejecting filler (the culled set is
untracked candidates, not curated rows). The canonical *measured* instance is the **+1.0
freshness lift**: a 2026 regulatory change where the bare model gave a stale answer and the
grounded, dated, provenance'd pipeline gave the correct one (live, via Ollama) — the canonical
proof of "what an export can't freeze." Per the honesty rule: the gate report and the +1.0
instance are real and computed; the *distribution* of lift across many wedge families is thin and
is the flywheel's job (do not read either as a broad shipped metric).

---

## 6. The data plane — registry, vector store, row families, and the honest gap

**Schema contract.** Components are schema-validated envelopes (`schemas/`); the universal,
load-bearing fields (`id`, `type`, `version`, `lifecycle`, `license`) live in the closed
envelope (`_common.schema.json`), and **everything else that grows is attribute-level**:
`dimension-record` (EAV: typed measurements/facets), `label-record` (tags), and **open
vocabularies** (`vocabularies/*.yaml`, validated in CI, not frozen enums)
([[../../codex/schema-extensibility.md]]). Adding the 40th dimension or a new process kind is
**zero schema change**. The one closed enum that matters — `componentType` (the 14 storage keys)
— is closed for good reason: it is the partition key.

**ID & hash discipline** (CLAUDE.md): generated IDs carry stable hash suffixes so daily batches
don't collapse during dedupe/index-merge; canonical hashes cover the normalized body, the version
definition, source content, index identity, command-approval, and CDC/replay events. A
*formatting* change must not mint a new version; a *content* change must — hash the normalized
body, not the wrapper.

**Row families** a scalable batch emits or preserves (CLAUDE.md): `source_record`,
`normalized_object`, `canonical_entity`, `object_entity_ref`, `dedupe_cluster`,
`label_assignment`, `dimension_value`, `object_embedding`, `index_record`, and `review_ticket`
when risk warrants. The **promotion boundary** is explicit: a candidate can be *load-ready*
(source + dedupe + content hash + index) while still **not** tenant-visible if it has open/
high-risk review, placeholder embeddings, unresolved provenance, or volatile facts without
CDC/revocation. `scripts.db.daily_promotion_readiness_plan` is the gate.

**Counts — computed, honest, and as of the README stats block (`scripts/build_readme_stats.py`,
no hand-typed numbers):**

- **2,511** schema-validated catalog manifests = **599** committed to git + **1,912**
  machine-generated candidates pending review/promotion. (Generated candidates are *not* shipped
  components — the promotion boundary is the line.)
- Loaded into the derived query DB (`dist/catalog.sqlite`): **505** objects, **1,024**
  relationship edges, **0 embeddings**.
- **13 emitters** under `scripts/emit/` (precise; the standards crosswalk — §8).

> **The #1 honest gap, stated plainly:** **0 embeddings today.** Hybrid keyword+vector+graph
> search and promotion gate #6 (vectorization) both block on real embeddings; `stage_load` flags
> them `placeholder`. The embedding model + dimension are single-sourced (`scripts/_config.py`),
> the pgvector bootstrap exists (`infra/postgres/`), and this is the cheapest, highest-leverage
> unblock on the roadmap. A reviewer should treat retrieval as *architected and bootstrapped, not
> yet populated.* This is the most important "planned vs active" line in the whole asset.

---

## 7. Runtime, orchestration & cost governance

**Phase model** ([[../../architecture/cloud-architecture.md]]): a **queue + worker tier is
non-negotiable; K8s is *earned*, not day-one.** Phase 1 (the wedge, ~$40–90/mo) is a managed
PaaS — Cloudflare/CDN → web/API (Render/Cloud Run) → managed queue (SQS/Cloud Tasks/Upstash) →
workers running `Foundry.run_partition` → Neon (Postgres+pgvector) + R2 + a light event bus.
Phase 2 (scale + enterprise) is K8s with **KEDA autoscaling on queue depth** (scale-to-zero) for
the 10×1k partition bursts, a workflow engine (Temporal / Argo Workflows) over the foundry DAG,
and **Helm + Terraform**.

**Provider-neutrality is structural, not aspirational.** Store / Queue / Embedder / model-route
are `from_env()` selectors, so adopting Cloudflare's AI stack (AI Gateway in front of every
provider, Workers AI for embeddings/small models, Pages for the static front-end, R2 for objects)
is *an adapter or an env var, never a rewrite* — and AI Gateway's per-request cost/usage maps
1:1 onto the billable events the meter already defines. The governed system-of-record stays
**pgvector co-located with the relational row families + provenance** (don't split governance
across two stores); Vectorize is an optional edge cache for hot, semantic-only public lookups.

**Cost governance is first-class** ([[../../architecture/cloud-architecture.md]] cross-cutting):
every async job carries a model-call budget; the worker meters the billable events
(`scripts/foundry/access.py` — `frozen_export` · `live_subscription` · `credentialed_data` ·
`hosted_endpoint` × `refresh` · `data_query` · `hosted_call`), so usage = revenue and runaway
cost is capped. **Honest status:** these billing *axes* are implemented and self-tested; the
*plumbing* (Stripe, a credits ledger, a meter-at-worker bridge) is a gap on the roadmap (§2.2
there) — do not read "billing axes implemented" as "billing wired."

**Telemetry** is one contract for every service (`services/platform/_shared/telemetry.py`):
structured JSON logs (building on `scripts/showcase/jsonlog.py`), Prometheus metrics
(`/metrics`), and OpenTelemetry traces spanning *enqueue → worker → store*; collectors in
`infra/observability/`. No service rolls its own logging, so a job is followable end to end.

---

## 8. Governance & provenance — the external moat

Governance is the moat a bigger model cannot copy ([[../../design/value-propositions.md]] claim
2): provenance on every fact, signed/verified publishers, live corpora with CDC freshness +
revocation, an accountable signer, and auditor-grade attestation. Three architectural pillars a
reviewer can verify:

- **Provenance/license spine.** Every row carries `source_url` + `license` + `author`; the
  foundry's `sources` stage enforces it and uncertain provenance routes to a `review_ticket`. No
  real PII/secrets/proprietary dumps — public or synthetic metadata only; `_reference/` is never
  republished.
- **Standards crosswalk — 13 emitters** (`scripts/emit/`, precise count): including
  `spdx_3.py`, `cyclonedx_ml.py` (SBOM), `c2pa.py` (signed content provenance),
  `eu_ai_act_annex_iv.py` (Art. 11 evidence), `openlineage.py`, plus delivery/eval emitters
  (`mcp_server.py`, `agent_skill.py`, `promptfoo.py`, `lm_eval_harness.py`, `croissant.py`,
  `hf_*`). This is the supply-chain + regulated-buyer evidence surface, generated from the
  governed rows — not bolted on.
- **Freshness / CDC / revocation.** The governance service (scheduled, active) runs promotion
  readiness and emits `promotion.ready` / `cdc.changed`; scrapers capture `scraped_at` +
  `source_url` + `license` so every volatile fact is dated and attributable. **Honest status:**
  the emitters and billing axes are implemented and proven once (the +1.0 instance); *operating*
  the moat live — scrapers on a cadence, CDC/revocation propagation to subscribers, C2PA
  signing-key infra — is the roadmap's Arc-B work, not shipped.

The freezable-vs-recurring boundary falls straight out of this: **freezable** (static text/info
components, raw + compressed tiers) is the free funnel and one-time/storage revenue; **recurring**
is the live, CDC-fresh governed layer and build-on-demand — *because a static download can't stay
current.* That CDC/freshness obligation is the recurring-revenue moat.

---

## 9. Deployability — BYO-cloud / air-gap (the acquisition lever)

The whole stack is designed to run in a customer's — or an acquirer's — own infrastructure, which
is simultaneously the enterprise tier and a clean integration story for a buyer. Three properties
make it real rather than a claim:

- **One image, role-per-command** (§2) and **stateless, queue-driven workers** — the Phase-1→
  Phase-2 move is *configuration, not a rewrite*. `infra/` carries the Dockerfile (role per
  command), `infra/docker-compose.platform.yml` (local topology), `infra/k8s/` (cloud), and
  `infra/airflow/dags/` (scheduled DAGs).
- **Provider-neutral data + model layers** (`from_env()` selectors), so the governed core is
  portable and the data layer is not locked to any vendor — portability *is* the moat and the
  BYO-cloud/air-gap story.
- **Helm + Terraform (Phase 2, specified)** → a lab can stand up the entire governed engine +
  corpora + measurement harness in its own VPC or an air-gapped enclave. Marked **planned**:
  specified in the cloud architecture, not yet stood up in a cloud account (see the roadmap §2.1).

For a regulated wedge that needs FedRAMP/HIPAA, the recommended split is data-gravity-aware
([[../../strategy/recommended-stack-and-cloud.md]]): edge/storage/serving on R2+Workers (zero
egress), heavy GPU (vLLM, embedding-at-scale, foundry, measurement) on a GPU cloud co-located
with its pgvector + Postgres, serving only finished artifacts from R2.

---

## 10. What a reviewer should verify (and the honest seams)

**Verify directly (active today):**

- `python3 -m scripts.foundry.pipeline --self-test` → the eight-stage evidence-gated loop passes
  offline, including the anti-filler assertion and human-approval routing.
- `services/registry.yaml` → the service map, with `status` marking active vs planned.
- `dist/reports/capability-lift-gate.json` → the lift floor (0.2) and the cull (1,980 / 4,377).
- `scripts/build_readme_stats.py` → the computed catalog counts (no hand-typed numbers).
- `scripts/eval/reason_codes.py` → the single-source durability taxonomy.
- `catalog/processors/verify/compression-fidelity-check.yaml` → the tier-fidelity component (the
  shared measurement engine extended to Baltor).
- `scripts/emit/` → the 13 standards emitters.

**The honest seams (planned / partial — sourced to the roadmap gap analysis,
[[../../strategy/acquihire-roadmap.md]] §2):**

| Asset | State | Where |
|---|---|---|
| Real embeddings / hybrid search | **0 today** — the #1 blocker; bootstrapped, not populated | §6 here; roadmap §2.7 |
| Baltor `enrichment` tier pipeline | `planned` — components seeded, no tier entrypoint | registry; [[../../strategy/context-enrichment-service.md]] |
| Billing plumbing (Stripe/credits/meter-bridge) | axes built, plumbing **gap** | §7 here; roadmap §2.2 |
| Backend auth + multi-tenancy | front-end only; backend identity **gap** | roadmap §2.3 |
| Phase-1 cloud deploy / Phase-2 K8s + Helm/Terraform | **designed**, not stood up | §9 here; roadmap §2.1 |
| Live governed layer (scraper cadence · CDC propagation · C2PA keys) | emitters built + proven once; live operation **partial** | §8 here; roadmap §2.4 |

**The thesis a reviewer should leave with:** the durable asset is the **architecture that makes a
governed component trustworthy** — the seven-primitive grammar (the format layer), the
evidence-gated foundry (filler is impossible by construction), the shared measurement engine
(lift *and* fidelity, externally validated), the attribute-level governed data plane, and the
provider-neutral, BYO-cloud-deployable substrate — sold through **two doors with one COGS**. The
volume and the live layer are the flywheel's job and are honestly marked unfinished; the
*machinery that makes them defensible* is built and self-tested.

---

*Grounds: `services/registry.yaml`; `docs/strategy/{two-services-shared-infrastructure,
context-enrichment-service,recommended-stack-and-cloud,context-layer-pmf,acquisition-positioning,
acquihire-roadmap}.md`; `docs/architecture/{backend-services-and-platform,cloud-architecture}.md`;
`docs/codex/{master-goal,no-magic-values,schema-extensibility,change-verification-contract}.md`;
`docs/concepts/{component-taxonomy-and-stages,context-layer-and-the-desk}.md`;
`docs/design/value-propositions.md`; `scripts/foundry/` (21 modules; `pipeline.py --self-test`
passes); `scripts/eval/reason_codes.py`; `scripts/emit/` (13 emitters);
`catalog/processors/verify/compression-fidelity-check.yaml`;
`dist/reports/capability-lift-gate.json`; `scripts/build_readme_stats.py` (computed counts);
`scripts/_config.py` (embedding model/dim single source); `infra/postgres/` (pgvector bootstrap).*
