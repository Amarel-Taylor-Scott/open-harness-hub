# Backend services & the shared platform plane

How the backend is organized into **two product services over one shared platform plane** — the
backend counterpart to the per-product front-end split ([[../strategy/two-services-shared-infrastructure.md]]).
Extends [[cloud-architecture.md]] (the 4-tier request/async/scheduled/data model) with the
**product-service** dimension and the **service/folder boundaries**. Nothing here forks the engine;
`scripts/` stays the implementation, `services/` is the thin service layer, `infra/` is the topology.

## The model: 2 product services × 1 shared platform × 4 tiers

```
   ┌──────────────────────────────┐      ┌──────────────────────────────┐
   │  PRODUCT SERVICE: harness-hub │      │ PRODUCT SERVICE: context-     │   ← request tier
   │  serves web/harness-hub/ +    │      │ enrichment — serves           │     (one per product,
   │  OHH API (build · monitor)    │      │ web/context-enrichment/ +     │      OH_PRODUCT-pinned)
   │  EMBER                        │      │ CEaaS API + MCP serve · TEAL  │
   └───────────────┬──────────────┘      └───────────────┬──────────────┘
                   │   both call the SAME shared platform │
                   ▼                                      ▼
   ┌───────────────────────────  SHARED PLATFORM PLANE  ───────────────────────────┐
   │  ingestion · foundry · measurement · enrichment · retrieval · governance        │
   │  (the shared backend services — one set of code, two consumers)                 │
   │                                                                                  │
   │  async tier   queue (RedisQueue protocol → Celery/Argo adapters) + worker fleet  │
   │  scheduled    cron / Argo / Airflow(Composer) DAGs — daily factory, re-embed,    │
   │               freshness/CDC, promotion readiness, decay re-benchmark             │
   │  data tier    Postgres + pgvector · object store (R2/S3) · Redis broker · bus    │
   │  cross-cut    telemetry (OTel + Prometheus + structured JSON logs) · governance  │
   └──────────────────────────────────────────────────────────────────────────────┘
```

The two product services are **thin request-tier doors**; all heavy work is the shared platform,
reached **synchronously** (read APIs) or **asynchronously** (enqueue a job). One governed object,
two doors — same provenance, same lift/fidelity scores ([[../strategy/context-enrichment-service.md]]).

## Service catalog (the boundaries — single source of truth: `services/registry.yaml`)

| Service | Tier | Owns (`scripts/`) | Entry / command | Talks to | Scale |
|---|---|---|---|---|---|
| **harness-hub** (product) | request | `showcase` (web) | `services/products/harness_hub` → `python -m scripts.showcase` (`OH_PRODUCT=harness-hub`) | enqueue→queue; read→retrieval/db | RPS / HPA |
| **context-enrichment** (product) | request | `showcase` (web) + MCP serve | `services/products/context_enrichment` (`OH_PRODUCT=context-enrichment`) | enqueue→queue; read→retrieval/enrichment | RPS / HPA |
| **ingestion** | async/sched | `ingest`, `acquisition` | `scripts.ingest.feed` / `.freshness` / `.health` / `.run` | source bus → normalize → store | KEDA on queue |
| **foundry** | async | `foundry`, `factory` | `scripts.foundry.worker --serve` (`Foundry.run_partition`) | queue ⇄ measurement, store | KEDA on queue depth |
| **measurement** | async | `eval`, `verification` | `scripts.eval.*` (lift), `verify.compression_fidelity` (tier fidelity) | called by foundry/enrichment | job |
| **enrichment** (CEaaS) | async | `processors/{compression,memory,cache,retrieval}` | tier pipeline: structural/learned compress · distill · cache · embed | queue ⇄ store, retrieval | KEDA |
| **retrieval** | request/async | `db` (vector), `processors/retrieval` | vector/lexical/hybrid/graph query | reads pgvector | RPS |
| **governance** | async/sched | `db` (promotion/CDC), `_publish` | promotion readiness · CDC · provenance · signing | event bus, store | job |
| **worker** | async | — (runs platform jobs) | `scripts.foundry.worker --serve` or `services/worker` (Celery) | pulls queue | KEDA scale-to-zero |
| **scheduler** | scheduled | — (triggers jobs) | cron / Argo / Airflow DAGs (`infra/airflow/dags/`) | enqueues to queue | 1 |
| **data plane** | data | — | Postgres+pgvector · object store · Redis · bus | — | managed |

## Communication (no shared mutable state between services)

- **Sync (request):** product services call read APIs (`/api/*`, retrieval) for low-latency lookups.
- **Async (jobs):** everything bursty/long/cost-gated is a **job on the queue** — the `Queue`
  protocol in `scripts/foundry/queues.py` (default `RedisQueue`; **Celery/Argo/SQS adapters opt-in** —
  see Orchestration). Jobs are idempotent dicts; the foundry's content-hash + resumable ledger converge
  on re-runs. **Never run tier-2 work in a request handler.**
- **Events (bus):** CDC / freshness / decay / promotion emit events (pub/sub) that fan out to
  re-ingest, re-embed, revalidate. The product services subscribe only to what their surface needs.

## Containerization (one image, per-service role)

One Dockerfile, many roles — the web/API tier and every platform worker are the **same image**
started with a different command (the existing approach; keeps one build). Per-service commands +
env live in `services/registry.yaml`; local topology in `infra/docker-compose.platform.yml`; cloud
in `infra/k8s/`. Product services differ only by `OH_PRODUCT` (folder + brand) — identical backend.

## Orchestration (light by default, named adapters when earned)

Honors [[cloud-architecture.md]]: **a queue + worker tier is non-negotiable; heavy frameworks are
earned, not day-one.** So:
- **Default (low-ops):** `RedisQueue` + the built-in worker loop (retry/dead-letter) + Render/Cloud-Run
  cron. Runs the whole platform with one dep.
- **Celery adapter (scale/monitoring):** `services/worker/celery_app.py` — broker=Redis, **queues per
  concern**, beat for periodic. Opt-in; satisfies the same `Queue` role. Use when you want Celery's
  scheduler/Flower monitoring.
- **Airflow / Cloud Composer (scheduled DAGs):** `infra/airflow/dags/` — the multi-step scheduled
  pipelines (daily factory, re-embed, freshness sweep, promotion readiness) as DAGs with per-task
  retries + visibility. Sits **above** the queue. (Argo Workflows is the in-cluster alternative;
  `infra/k8s/argo-foundry.yaml`.)
- **K8s + KEDA (fleet):** autoscale workers on queue depth (scale-to-zero) for 10×1k partition bursts;
  earned by scale or enterprise BYO-cloud/air-gap. `infra/k8s/`.

## Telemetry (the gap this fills)

`services/platform/_shared/telemetry.py` — one import for every service: **structured JSON logs**
(building on `scripts/showcase/jsonlog.py`), **Prometheus metrics** (counters/histograms; `/metrics`),
and **OpenTelemetry traces** (spans across enqueue→worker→store). Config + collectors in
`infra/observability/` (otel-collector · prometheus · grafana), wired by the platform compose. No
service rolls its own logging; all emit the same trace/metric/log contract so a job is followable
enqueue→done across services.

## Folder structure (separation of concerns at every level)

```
scripts/        IMPLEMENTATION — libraries by concern (foundry, ingest, eval, db, processors…). Unchanged.
services/       SERVICE LAYER — one folder per service: entrypoint + contract + README. Imports scripts/,
                never moves it. registry.yaml is the single source of truth for the service map.
  products/{harness_hub,context_enrichment}/   the two product (request-tier) doors
  platform/{ingestion,foundry,measurement,enrichment,retrieval,governance}/  the shared plane
  platform/_shared/telemetry.py                the cross-cutting telemetry contract
  worker/        the async-tier worker + Celery adapter
  scheduler/     the scheduled-tier DAGs pointer
infra/          TOPOLOGY — Dockerfile (role per command), compose (local), k8s (cloud), airflow/dags,
                observability/ (otel·prometheus·grafana).
```

**Migration is non-breaking + incremental:** today `services/` entrypoints are thin wrappers over
`scripts/` (so imports + the documented fast-path keep working); logic migrates folder-by-folder into
the owning service over time. The boundaries, comms, and topology are defined now; the code moves
behind them without breaking callers.
