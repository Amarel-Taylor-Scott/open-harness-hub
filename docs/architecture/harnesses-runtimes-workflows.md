# Harnesses, runtimes & workflows — the improvement plan

**What this is:** a *design* (not code) catalogue of every **harness** (the governed recipes and
loops that produce work), **runtime** (where that work executes), and **workflow** (the operating
loops that drive the platform), each mapped to its real status in `services/registry.yaml`, plus a
**prioritized, warrant-tagged plan** to promote the `planned` ones — naming the *smallest real
entrypoint* for each. It is the "what's wired vs. what's seeded vs. what's a stub" map an engineer
needs before touching the platform.

This **references, does not duplicate**, [[backend-services-and-platform.md]] (the service/folder
boundaries, the comms model, telemetry) and [[cloud-architecture.md]] (the 4-tier request/async/
scheduled/data model + orchestration ladder). Read those for the *topology*; read this for the
*feature inventory and the promotion plan*.

> **Warrant.** Owner intent — "catalogue the harnesses/runtimes/workflows, map each to registry
> status (active vs planned), and give a prioritized plan to promote the planned ones, esp. the CEaaS
> enrichment tier + `verify.compression_fidelity`." Corroboration for every status claim below: the
> live code (foundry/worker/queue self-tests pass offline; the Celery/Airflow modules are import-safe
> opt-in stubs), `services/registry.yaml` (`active` vs `planned`), and the directory tree
> (the `enrichment` service's `owns:` paths do not yet exist as code). Established principle:
> the change-verification contract's **honest-status** rule — *seeded definitions and stubs are
> not shipped features* — and the capability-lift / measured-fidelity bar.

## Three words, one distinction

The word **harness** is overloaded in this repo on purpose; keep the three senses separate:

- **The governed recipe / foundry** — the *production* harness: the eight-stage evidence pipeline that
  mints components only on measured lift (`scripts/foundry/`). This is a backend feature.
- **A catalog Action** — in product vocabulary a persona/tool/processor/**harness**/rubric is all just
  an **Action** (the seven-primitive grammar). A "harness" you wire into a pipeline is a catalog row,
  not infrastructure.
- **The agent operating loops** — `/goal`, `/launch`, `/evolve`, `/polish`: the autonomous *workflows*
  that drive *development of* the platform. These are `.claude/commands/*.md`, not product surfaces.

This doc covers the first and third senses (infrastructure + operating loops); the second is the
catalog, governed by [[../concepts/component-taxonomy-and-stages.md]].

---

## 1 · Harnesses (the recipes and loops that produce work)

| Harness | What it does | Entrypoint | Owning service | Status |
|---|---|---|---|---|
| **Governed recipe / foundry** | 8-stage evidence pipeline: gaps → sources → construction → standardize → novelty → **measure (lift)** → gate → stage_load. Reports **promoted**, never generated. | `python -m scripts.foundry.pipeline` (`--self-test`/`--demo`); fleet via `Foundry.run_fleet` | foundry | **active** — self-test green offline |
| **Foundry worker (partition consumer)** | Pulls partition jobs off the queue, runs `Foundry.run_partition`, wires a live model route from env if present, persists row families, retry + dead-letter. | `python -m scripts.foundry.worker --serve` (`--self-test`/`--demo`) | foundry / worker | **active** — self-test green |
| **Lift measurement engine** | Stage-5 `pipeline_score − bare_model_score` on held-out tasks; deterministic token-F1 offline, pluggable `BareModel`/`PipelineRunner`/`Judge` for live. **Never fabricates a delta** (unmeasured → review). | `python -m scripts.foundry.measure`; `scripts.eval.durable_gap_harness`; taxonomy in `scripts.eval.reason_codes` | measurement | **active** |
| **Demand / interaction harness** | Logs every interaction (redacted, consent-gated, hashed), mines unmet demand → capability-requests + research-queue areas. The model-independent gap signal. | `python -m scripts.foundry.interactions` (`--mine`) | foundry | **active** |
| **Gap screen + research queue** | Cheap Stage-1 gap screen (model-independent weighted) → ranked research areas the owner feeds. | `scripts/acquisition/gap_screen.py`, `research_queue.py` | foundry / measurement | **active** |
| **CEaaS enrichment tier pipeline** | raw → compressed (structural + learned) → hyper-efficient (distill + cache-shape), hosted + downloadable, the four delivery surfaces. | *none yet* — `enrichment` service `command` is TBD | enrichment | **planned** — see §4 |
| **`verify.compression_fidelity` harness** | "Did this tier preserve enough?" — quality delta per tier, by a *separate* evaluator. The CEaaS moat; same engine as the lift gate. | *none yet* — seeded as a catalog definition only (`catalog/processors/verify/compression-fidelity-check.yaml`) | measurement | **planned** — see §4 |

**The load-bearing honest distinction.** The foundry, worker, queue, measurement, and interaction
harnesses are **real** (their `--self-test`s pass offline today). The two CEaaS harnesses are
**seeded governed definitions, not running code**: `scripts.seed.ceaas_components` wrote the catalog
YAMLs (`compression/structural-compress`, the four `deliver/*` surfaces, `verify/compression-fidelity-check`),
and the `enrichment` service in `services/registry.yaml` declares
`owns: [scripts/processors/{compression,memory,cache,retrieval}]` — **but those directories do not
exist yet.** A seeded component is a promise with provenance; it is not a feature until an entrypoint
runs it under measured fidelity. The spec is explicit about this (CEaaS is "spec-level… components are
seeded… implementation to make CEaaS real" — [[../strategy/context-enrichment-service.md]]).

---

## 2 · Runtimes (where the work executes)

The platform runs **one image, many roles** (one Dockerfile started with different commands; per-role
command + env in `services/registry.yaml`). Local topology in `infra/docker-compose.platform.yml`,
cloud in `infra/k8s/`. See [[backend-services-and-platform.md]] §Containerization.

| Runtime | Role | Where defined | Status |
|---|---|---|---|
| **Local Python (stdlib)** | Run any harness `--self-test`/`--demo` with zero services; the durable local broker is `SqliteQueue`, the local store is `SqliteStore`. | `scripts/foundry/{queues,store}.py` `from_env()` | **active** — the default dev path |
| **Docker (single + platform)** | Per-role containers from one image. | `infra/docker-compose.yml`, `infra/docker-compose.platform.yml`, `infra/postgres/` | **active** (compose files present) |
| **Kubernetes** | Per-service Deployments (web, worker, cron, freshness-cron, core). KEDA autoscales workers on queue depth (scale-to-zero). | `infra/k8s/{web,worker,cron,freshness-cron,core}.yaml` | **active** (manifests present) |
| **Default broker — RedisQueue + built-in worker loop** | Redis-list queue (`rpush`/`lpop`/`llen`), KEDA-native; nack re-queues; dead-letter to `{key}:dead`. The non-negotiable queue+worker tier. | `scripts/foundry/queues.py` (`RedisQueue`), `worker.py` | **active** — self-test green (offline via fake-redis) |
| **Celery adapter (opt-in)** | Per-queue routing (`foundry,ingest,enrich,measure`), beat scheduler, Flower monitoring. Tasks shell out to the *same* real modules cron/Airflow run — no logic forked. | `services/worker/celery_app.py` (`requirements-platform.txt`) | **opt-in adapter** — import-safe stub; prints "NOT installed" without the extra |
| **Airflow / Cloud Composer (opt-in)** | The multi-step scheduled DAGs (freshness sweep, daily-factory→embed→promotion, corpus ingest) with per-task retries + backfill. Sits *above* the queue. | `infra/airflow/dags/ohh_platform_dags.py` | **opt-in adapter** — defines nothing if `airflow` absent |
| **Argo Workflows (opt-in)** | In-cluster alternative to Airflow for the foundry DAG. | `infra/k8s/argo-foundry.yaml` | **opt-in adapter** |
| **Telemetry** | One import for every service: structured JSON logs (built on `scripts/showcase/jsonlog.py`) + Prometheus `/metrics` + OTel traces (enqueue→worker→store). Degrades to no-op if the optional libs are absent. | `services/platform/_shared/telemetry.py`; collectors `infra/observability/` | **active** (logs always; metrics/traces when extras installed) |
| **Datastores** | Postgres+pgvector (operational + vector), object store (R2/S3, tiered artifacts), Redis (broker + cache), event bus (CDC/freshness/promotion). | `services/registry.yaml` `datastores:` | local SQLite **active**; cloud datastores wired per deployment |

**Honest framing for the opt-in adapters.** Celery, Airflow, and Argo are *earned, not day-one*
([[cloud-architecture.md]] orchestration ladder). They are real, import-safe wrappers over the same
module entrypoints — but they only activate with `requirements-platform.txt` installed. The default
runtime (RedisQueue + the built-in worker loop + cron) runs the **whole platform with one dependency**.
Do not present "Airflow DAGs" as a shipped capability; present it as the documented scale path.

---

## 3 · Workflows (the loops that drive the platform)

Two families: the **autonomous operating loops** (how agents *build* the platform) and the **platform
data workflows** (how the platform *runs itself*).

### 3a · Autonomous operating loops (`.claude/commands/*.md`)

These are agent *workflows*, not product features — the operating contract a Claude/Codex session
adopts to run for hours/days. They are governed by the **change-verification contract**
([[../codex/change-verification-contract.md]]): the prioritizer tags each item's warrant, a *separate*
verifier confirms it, the orchestrator commits only warranted + green increments.

| Loop | Drives | Status |
|---|---|---|
| **`/evolve`** | The umbrella loop over the whole two-product platform; subsumes the others, picking the weakest lane each cycle (ORIENT→PLAN→BUILD→VALIDATE→RECORD→BRANCH). | active (`.claude/commands/evolve.md`) |
| **`/goal`** | The factory loop (P1–P2): run the evidence-driven foundry; metric is **promoted**, never generated. | active (`goal.md` → `docs/codex/master-goal.md`) |
| **`/launch`** | Bring up **both** product surfaces behind persistent tunnels and keep them launch-quality. | active (`launch.md`) |
| **`/polish`** | Drive the OHH front-end so every surface *sells* its value prop. | active (`polish.md`) |
| **`/direction`** | The resilience contract: no terminal state, branch-on-block, safety-gates-are-not-stops. | active (`direction.md`) |

These multi-agent workflows are real and in use; their *output* (committed code, ledger lines) is what
moves the inventory below from `planned` to `active`. The **verifier is always a different agent than
the builder** — no self-grading (the contract's reason-for-existing).

### 3b · Platform data workflows (the recurring jobs)

The scheduled tier runs the same module entrypoints whether triggered by cron, Celery-beat, or
Airflow. The DAGs are defined identically across `services/worker/celery_app.py` (beat) and
`infra/airflow/dags/ohh_platform_dags.py`:

| Workflow | Steps | Cadence | Status |
|---|---|---|---|
| **Freshness / CDC sweep** | poll registered sources → enqueue reingest | every 30 min | active (entrypoint `scripts.ingest.freshness`) |
| **Daily factory → readiness** | `foundry.seeds --run` → `db.embedding_execution_plan` → `db.daily_promotion_readiness_plan` | daily 07:00 | active (entrypoints exist; embeddings still a known gap, master-goal P1) |
| **Corpus ingest** | feed every registered source into the governed corpus | daily, off-peak | active (`scripts.ingest.feed --all`) |
| **Enrichment tier build** | raw→compressed→hyper-efficient + fidelity | — | **planned** (queue `ohh:enrich:jobs`, no consumer) — see §4 |

> **Honest caveat (carry from `master-goal.md`).** The daily-factory DAG's *embedding* step is wired,
> but real embeddings remain the platform's P1 gap (0 committed embeddings; promotion is correctly
> blocked without a real vector). The workflow exists; the substrate it needs is the §4 work.

---

## 4 · The improvement plan — promote the `planned` features

Prioritized by *blast radius × how-blocked-the-product-is*, each with the **smallest real entrypoint**
(the minimum runnable thing that flips the status), and a warrant. The rule throughout:
**reuse the shared backend, add no new engine** — CEaaS is "a surface + a meter + emitters over the
same substrate" ([[../strategy/context-enrichment-service.md]]).

### P1 — `verify.compression_fidelity` as a real harness (the CEaaS moat)
- **Why first:** it is the *same measurement engine as the lift gate*, extended from "does the pipeline
  lift?" to "did the tier preserve?". Without it, the entire CEaaS value prop (measured fidelity per
  tier) is unbacked — and it gates every tier the enrichment pipeline would emit, so it must exist
  before §P2 is meaningful.
- **Smallest real entrypoint:** `python -m scripts.processors.verify.compression_fidelity --self-test`
  — a `MeasurementStage`-shaped module that takes `(raw, tier_output, eval_tasks)` and emits a
  `fidelity_delta` **`dimension-record`** scored by a *separate* evaluator (reuse `scripts.foundry.measure`'s
  token-F1 / `Judge` protocol offline; pluggable LLM-judge live). Self-test proves a lossy tier scores
  *below* a lossless one. This makes the seeded `verify/compression-fidelity-check.yaml` *executable*.
- **Reuse, don't rebuild:** `scripts.foundry.measure` (scoring + `Judge`), `scripts.eval.reason_codes`
  (durability), the EAV `dimension-record` schema (so the metric is attribute-not-column —
  [[../codex/schema-extensibility.md]]).
- **Warrant:** owner intent (named priority) + established principle (the measured-fidelity bar; the
  no-self-grading rule). **Bar:** substantive code → correctness verification (a passing self-test) +
  the principle.

### P2 — CEaaS enrichment tier pipeline (move `enrichment` planned→active)
- **Why second:** it is the headline CEaaS feature, but it *depends on* P1 (every tier it emits must
  ship a fidelity score). Today the `enrichment` service has a queue (`ohh:enrich:jobs`) and a declared
  ownership boundary but **no consumer and no code** (`scripts/processors/{compression,memory,cache,
  retrieval}` are absent).
- **Smallest real entrypoint:** create `scripts/processors/compression/structural.py` with one runnable
  tier — `compress.structural` (strip bodies, keep signatures; Repomix/Tree-sitter style) — behind
  `python -m services.platform.enrichment.worker --serve` pulling `ohh:enrich:jobs`, calling P1 for the
  fidelity delta, emitting `tier.built`. Start with the *one* freezable tier (structural compress) end
  to end before adding learned compression and the hyper-efficient (distill+cache) tier.
- **Then, incrementally (each its own runnable module under the same boundary):** `summarize.llmlingua`
  (learned), `memory/*` + `cache/*` (hyper-efficient, cache-shaped prefix), and the four
  `deliver/*` surfaces (`mcp_serve`, `llms_txt`, `skill_package`, `claudemd`) the YAMLs already define.
- **Reuse, don't rebuild:** the foundry worker loop + queue protocol (the enrichment worker is the
  same shape as `scripts.foundry.worker`), the store, telemetry. The service's `command:` in
  `services/registry.yaml` is filled in as each tier lands (the migration is non-breaking — wrappers
  first, logic moves behind the boundary).
- **Warrant:** owner intent (named priority) + corroboration (the spec's three-tier table, the
  Repomix/LLMLingua/Mem0 prior art it cites — [[../strategy/recommended-stack-and-cloud.md]]).
  **Bar:** design-adjacent build → corroboration + the reuse principle; keep tiers `experimental`
  until P1 fidelity scores back them.

### P3 — Real embeddings (unblock the daily-factory DAG and retrieval)
- **Why:** the daily-factory workflow's embed step and the `retrieval` service both depend on real
  vectors; promotion is correctly blocked without them (master-goal P1; gate 6).
- **Smallest real entrypoint:** wire a declared embedding model + dim through `scripts/_config.py` (one
  definition, no magic values — [[../codex/no-magic-values.md]]), embed the committed components, run
  `scripts/db/vector_readiness_audit.py` green. This is *already the named P1* in
  [[../codex/master-goal.md]]; it is repeated here because it is the precondition for the daily-factory
  DAG and the `retrieval`/`enrichment` runtimes to be more than wiring.
- **Warrant:** established principle (the master-goal's P1 exit criteria; the promotion boundary).

### P4 — Materialize the service-layer entrypoints behind their boundaries
- **Why:** today `services/` is thin wrappers over `scripts/`; the comms/topology are defined but most
  platform services have no dedicated entrypoint module yet (only `products/*`, `worker`, and
  `platform/_shared/telemetry` are present). This is *intended* (non-breaking incremental migration —
  [[backend-services-and-platform.md]] §Migration), but it is the difference between "boundary on
  paper" and "service you can deploy independently."
- **Smallest real entrypoint per service:** add `services/platform/{ingestion,foundry,measurement,
  retrieval,governance,enrichment}/entrypoint.py` that pins the role, calls `telemetry.configure(...)`,
  and hands off to the owned `scripts.*` module — exactly the pattern `services/products/
  context_enrichment/entrypoint.py` already demonstrates. Then point each registry `command:` at the
  new entrypoint.
- **Warrant:** established principle (the registry is the single source of truth; one telemetry
  contract per service). **Bar:** trivial/reversible additive scaffolding → self-evident correctness,
  recorded.

### P5 — Promote the opt-in orchestrators only when scale earns them
- **Why last:** Celery/Airflow/Argo are explicitly *earned, not day-one*. Promoting them before P1–P3
  is solved adds ops surface for no product capability.
- **Trigger + entrypoint:** when queue depth / DAG-visibility needs justify it, `pip install -r
  requirements-platform.txt` and switch the worker command to the Celery app (or point Composer at
  `infra/airflow/dags/`). No code change — the adapters already shell out to the same modules.
- **Warrant:** established principle (the orchestration ladder); promote on measured need, not
  speculation.

---

## Status legend (single source: `services/registry.yaml`)

- **active** — a real runnable entrypoint exists today (and, for harnesses here, a `--self-test`
  passes offline).
- **opt-in adapter** — real, import-safe code that activates only with a scale extra installed; the
  default path does not need it.
- **planned** — boundary + queue + (sometimes) a seeded catalog definition exist, but **no entrypoint
  runs it** and, for CEaaS, the `owns:` code directories do not yet exist.
- **seeded definition** — a governed catalog row (provenance, lifecycle) with no executing code. *Not a
  feature.*

When this doc and the registry disagree, **the registry wins** — fix this doc. Counts and component
totals are never hand-typed here (no-magic-values); see `python scripts/oh_hub.py stats` for live
catalog figures.

## Related

[[backend-services-and-platform.md]] · [[cloud-architecture.md]] ·
[[../strategy/context-enrichment-service.md]] · [[../strategy/two-services-shared-infrastructure.md]] ·
[[../strategy/recommended-stack-and-cloud.md]] · [[../codex/master-goal.md]] ·
[[../codex/change-verification-contract.md]] · [[../codex/schema-extensibility.md]] ·
[[../codex/no-magic-values.md]] · [[../concepts/context-layer-and-the-desk.md]] ·
[[../design/value-propositions.md]]
