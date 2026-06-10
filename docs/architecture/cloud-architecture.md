# Cloud Architecture — production topology (Render-now → K8s-at-scale)

> The question: web app on Render, but the platform also does **API calls, scrapers,
> and batch generation** — does that want **K8s + orchestration + a queue**? Short
> answer: **a queue + a worker tier are non-negotiable; K8s is *earned*, not required
> day one.** Keep the web tier on a PaaS; put the async work behind a queue; move the
> worker fleet to K8s when *scale* or *enterprise BYO-cloud* pulls you there.

## The core insight: this is not one app — it's four tiers

| Tier | Workload shape | What runs here |
|---|---|---|
| **Request** | low-latency request/response, autoscale on RPS | the product UI/API, search/recommend, the conversational builder, the **hosted-endpoint premium** (metered model proxy) |
| **Async worker** | bursty, long-running, retryable, rate-limited, **cost-gated** | the **foundry** (gap→source→construct→measure→gate→load), **scrapers**, lift **measurement** (model calls), **embeddings**, managed ingestion |
| **Scheduled** | cron | daily factory partitions, **re-scrapes + CDC**, decay re-benchmarks, freshness feeds |
| **Data** | stateful, managed | Postgres + **pgvector**, object storage, the **queue/broker**, cache, event bus |

The mistake to avoid is running tier-2 work inside tier-1 request handlers. Scrapers
and generation are **jobs**, not web requests — they belong behind a queue.

## Direct answers

- **Queue — yes, definitely.** A broker decouples bursty generation/scraping from the
  API and gives you retries, rate-limiting, **per-job cost budgets** (the foundry's
  `FoundryConfig.model_call_budget` maps straight to this), backpressure, and idempotent
  replay. This is the single most important piece.
- **Orchestration — yes, at the right level.** The foundry is a multi-stage DAG, so a
  workflow engine (**Temporal / Argo Workflows / Prefect**) buys durable per-stage
  retries + visibility + resumability. *But* the foundry is **already** built as discrete
  stages with a **funnel ledger** (resumable) and `run_fleet()` fan-out — so you can
  start with **a plain queue + the built-in ledger resumability** and add an orchestrator
  only when multi-stage failure-handling/visibility actually hurts.
- **K8s — not day one.** Render background workers + a managed queue do the same job with
  far less ops. K8s is earned by (1) **scale** — precise fleet autoscaling on queue depth
  (KEDA, scale-to-zero) for the 10×1k partition bursts; and (2) **enterprise** —
  BYO-cloud / VPC / **air-gapped** deploys via Helm/Terraform (also a strong acquisition
  asset: a lab can run the whole stack in *their* infra). Design for K8s now
  (containerized, queue-driven, stateless workers); run on Render until those pull you.

## Phase 1 — managed PaaS (MVP / the wedge) — low ops, ship fast

```
[ Cloudflare/CDN ]
      │
[ Web/API service ]  Render or Cloud Run — UI, registry API, builder, hosted-endpoint proxy
      │  enqueue jobs
[ Queue ]  Cloud Tasks / SQS / Upstash Redis (+ RQ/Celery/arq workers)
      │  consumed by
[ Worker service(s) ]  Render background workers / Cloud Run jobs — run foundry partitions,
      │                 scrapers, measurement, embeddings (each = `Foundry.run_partition`)
[ Scheduler ]  Render cron / Cloud Scheduler — daily factory, re-scrapes, decay re-benchmarks
      │
[ Data ]  Neon (Postgres + pgvector) · R2/S3 (snapshots, exports, bundles) · Redis (cache)
          · a light event bus (pub/sub) for CDC / freshness / decay alerts
```

Concrete: hosting starts ~$40–90/mo (the monetization brief's anchor) — Cloudflare Pages +
Neon pgvector + a worker + R2. Workers are **the same container** as the web tier, started
with a different command (`python -m scripts.foundry.seeds --run` / a queue consumer), so
there's one image to build.

## Phase 2 — K8s (scale + enterprise/BYO-cloud)

```
GKE / EKS:
  • Deployment: web/API (HPA on RPS)
  • Deployment: queue-consumer workers  ──KEDA──> autoscale on QUEUE DEPTH, scale-to-zero
  • CronJobs: scrapers, CDC re-scrape, decay re-benchmark
  • Jobs: one-shot batch partitions (10×1k)
  • Workflow engine: Temporal / Argo Workflows for the foundry DAG (durable retries, visibility)
  • Managed Postgres+pgvector (Cloud SQL/AlloyDB/RDS or Neon) · object store · Redis · NATS/PubSub
  • Helm chart + Terraform → reproducible, and deployable into a CUSTOMER'S / LAB'S cloud
    (BYO-cloud / VPC / air-gap) — the enterprise tier and an acquisition lever.
```

KEDA scaling **on queue depth** (not CPU) is the right primitive for the foundry's bursty
10×1k fan-out: idle → 0 workers; a queued batch → scale to N → drain → back to 0.

## Component → infra mapping

| Component / surface | Tier | Phase-1 home | Phase-2 home |
|---|---|---|---|
| Product UI + registry API + builder | request | Render/Cloud Run web | K8s Deployment + HPA |
| **Hosted-endpoint premium** (`model_route` proxy, metered) | request | web service + metering | K8s Deployment |
| **Foundry** partition (`run_partition`) | async | queue → Render worker | queue → K8s worker (KEDA) / Argo |
| **Scrapers** (gov source surfaces, provenance + CDC) | scheduled+async | Render cron → queue → worker | K8s CronJob → queue → worker |
| Lift **measurement** (model calls, cost-gated) | async | worker (budget per job) | K8s worker, budget per job |
| **Embeddings** (pgvector) | async | worker → Neon pgvector | worker → managed pgvector |
| **Human approval queue** (knowledge pending_human) | request+state | API + Postgres `review_ticket` | same |
| **CDC / freshness / decay alerts** | scheduled+events | cron + pub/sub → webhooks | CronJob + NATS/PubSub |
| Postgres+pgvector / object store / queue | data | Neon · R2 · Upstash | Cloud SQL · S3/GCS · SQS/NATS |

## Cross-cutting

- **Cost governance is first-class.** Every async job carries a model-call budget; meter
  `refresh` / `data_query` / `hosted_call` (the billing events from `access.py`) at the
  worker so usage = revenue and runaway cost is capped. The queue enforces concurrency +
  rate limits against model/API providers.
- **Idempotency + provenance.** Foundry stages are content-hashed and the funnel ledger is
  resumable, so a retried/duplicated job converges (no double-promotion). Scrapers capture
  `scraped_at` + `source_url` + `license` so every fact is dated and attributable.
- **Secrets/keys** (model routes, scraper creds) in a secrets manager (not env files in the
  repo), injected per service.
- **Observability**: structured logs + the funnel ledger + run traces (the `PipelineObject`
  is already a replayable audit record) → a metrics/telemetry store (the repo anticipates
  BigQuery/ClickHouse telemetry).

## Edge option — Cloudflare (AI Gateway · Workers AI · Vectorize)

Cloudflare's AI stack fits **because the engine is already provider-neutral** — Store / Queue /
Embedder / model-route are `from_env()` selectors, so Cloudflare is an *adapter or an env var*,
never a rewrite. Adopt it for the edge/cost wins; keep the governed core portable (portability
is the moat + the BYO-cloud/air-gap enterprise story — don't lock the data layer to any vendor).

| Cloudflare service | What it buys us | How it plugs in | Verdict |
|---|---|---|---|
| **AI Gateway** | One proxy in front of every model provider: caching, rate-limit, **multi-provider fallback**, per-request cost + analytics | `OH_LLM_BASE_URL` / `OH_EMBED_BASE_URL` → the gateway (it's OpenAI-compatible). **Works today, env-only, zero code.** Its per-request cost/usage is exactly the `hosted_call`/`data_query` billable events `access.py` meters. | **Adopt now** — turns the cost-governance section from aspiration into a dashboard. |
| **Workers AI** | Serverless **edge inference** for small / router / embedding models — no GPU ops, global low latency | `OH_LLM_BACKEND=http-openai` + `OH_LLM_BASE_URL=<workers-ai>` for the *right-sized* model step; `OH_EMBED_*` for embeddings. Mostly env-only. | **Adopt for embeddings + small/router models** — it *is* the "smallest model that clears the bar" recipe step + the narrow-task-to-cheap-model thesis. Frontier calls still route to hosted providers. |
| **Vectorize** | Managed, globally-distributed vector index | A pluggable vector-store/Embedder adapter (the `Index` / `build_vector_store` layer is already swappable). | **Complementary, add at search-scale** — an *edge read layer for the OPEN/public corpus search*; **pgvector (Neon/Cloud SQL) stays the transactional governed store** co-located with the relational row families + provenance. Don't split governance across two stores. |
| **Pages / Workers** | Edge-serve static assets globally | The product front-end (`web/`) is **no-build static** — a native Pages fit; `/api/*` proxies to the request tier. | **Adopt for the front-end.** |
| **R2** | S3-compatible object store (export bundles, raw scraped content, signed attestations) | Already the Phase-1 object store in the mapping above. | **Already planned.** |
| **Cloudflare Queues / Durable Objects** | Managed broker / stateful coordination | Behind the `Queue` protocol (`queues.from_env()`), an alternative to Redis/SQS. | **Adapter, optional** — Redis/SQS already cover Phase 1–2. |

Net: **AI Gateway + Workers AI (embeddings & small models) + Pages + R2 are an immediate, low-risk
Phase-1.5** that cuts model cost/latency and makes metering real; **Vectorize + Queues are
adapters to add when public-search or broker scale demands.** Keep pgvector as the governed
system-of-record so the moat (provenance, CDC, signing) stays in one transactional place.

```bash
# AI Gateway in front of the existing OpenAI-compatible route — no code change:
export OH_LLM_BACKEND=http-openai
export OH_LLM_BASE_URL="https://gateway.ai.cloudflare.com/v1/<acct>/<gw>/workers-ai/v1"
export OH_LLM_API_KEY="…"            # cached, rate-limited, multi-provider fallback, metered
export OH_EMBED_BASE_URL="https://gateway.ai.cloudflare.com/v1/<acct>/<gw>/workers-ai/v1"
```

## The decision

**Start Phase 1** (Render/Cloud Run web + a queue + workers + Neon pgvector + R2) — it
covers the API/scraper/batch needs with low ops and gets the wedge to revenue. **Build
for Phase 2 from day one** by keeping workers (a) containerized, (b) stateless, and (c)
queue-driven — so the move to K8s + KEDA + an orchestrator is *configuration, not a
rewrite*, and unlocks scale **and** the BYO-cloud/air-gap enterprise + acquisition story.
The foundry's stage/partition/ledger design is already shaped for exactly this.

---

*Grounds: `scripts/foundry/` (stage/partition/ledger design — already queue-ready;
`run_fleet` = the fan-out; `model_call_budget` = per-job cost gate), `scripts/foundry/access.py`
(billable events to meter at the worker), `scripts/foundry/model_route.py` (the hosted-endpoint
proxy + scraper/measurement model calls). Related in-repo: `docs/architecture/object-factory-worker-fleet.md`,
`containerized-object-factory-orchestration.md`, `low-cost-hosting-plan.md`,
`hybrid-postgres-bigquery-hosting.md`, `saas-operating-platform.md`,
`docs/strategy/monetization-mechanisms.md`, `infra/postgres/` (the pgvector bootstrap).*
