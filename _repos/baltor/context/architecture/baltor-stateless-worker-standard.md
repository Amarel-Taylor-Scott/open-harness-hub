# Baltor Stateless Worker Standard

Baltor workers should be small, stateless, idempotent, and easy to run locally
or in Kubernetes. A worker owns a capability, not state.

State lives in durable systems:

- Postgres/source ledger
- object storage for raw, extracted, and exported artifacts
- vector, keyword, and graph indexes
- queue/orchestrator metadata
- run/event ledger

Workers receive task envelopes and emit structured evidence, artifact URIs,
child tasks, confidence, escalation signals, and deterministic artifacts when
they discover reusable procedures.

## Task Envelope

```json
{
  "task_id": "cw-...",
  "run_id": "run-...",
  "tenant_id": "tenant-...",
  "capability": "web.price.check",
  "lane": "research",
  "priority": "normal",
  "scope": {
    "privacy": "tenant",
    "allowed_domains": ["example.gov"],
    "blocked_domains": [],
    "max_pages": 25,
    "max_cost_usd": 0.25,
    "deadline_s": 120
  },
  "input": {
    "query": "current filing fee",
    "source_uri": "s3://...",
    "context_refs": []
  },
  "output_contract": "evidence_packet",
  "model_policy": {
    "lane": "deterministic|small|medium|frontier",
    "allow_remote": false
  }
}
```

## Worker Classes

| Class | Purpose | Example capabilities |
|---|---|---|
| `source-sync` | Detect source changes and create version events. | Drive/SharePoint/Git/S3 sync, website sitemap scan. |
| `fetch` | Fetch one URL/API/object safely. | price page, statute page, company profile. |
| `browser-research` | Browse scoped sites with limits and evidence capture. | find latest address, browse government site for a fact. |
| `doc-process` | Extract and normalize uploaded content. | OCR, layout, tables, hierarchical chunking. |
| `context-analyze` | Work over processed chunks. | entities, claims, procedures, fragile-section ranking. |
| `graph` | Create or repair nodes and edges. | corporate hierarchy, source-to-claim graph, M&A relation edges. |
| `verify` | Check facts against sources. | statute citation, latest price, current address, source precedence. |
| `model-reason` | Use local/hosted models within bounded tasks. | reconciliation candidate, provenance summary. |
| `hermes` | Open-ended investigation for unresolved cases. | search many sources, produce resolution artifact. |
| `openclaw` | Adversarially test proposed resolutions. | counterexamples, overreach tests, scope boundaries. |
| `compile` | Turn non-deterministic solutions into reusable deterministic artifacts. | resolver rule, extraction template, query template. |

## External Research Capabilities

The same standard should cover:

- visit a website and check price information;
- visit a government website and read a published statute;
- browse a government site and find a specific fact;
- search for the latest business address;
- find the corporate hierarchy of a business;
- look for M&A news about employment agencies;
- look up capability or documentation for a function, class, API, or library;
- monitor a source for changes and enqueue downstream refresh jobs.

External research tasks must return source URLs, retrieval timestamps, extracted
answers, evidence spans or structured evidence, confidence, freshness labels,
next recommended tasks, and unresolved reasons when the worker cannot prove the
answer.

See `baltor-source-trust-and-adoption-policy.md` for multi-source adoption,
fact-state lineage, archive capture, publisher trust scoring, and injection/spam
screening.

See the **Queue lanes**, **Priority signals and default policy**, **Shared state
model and fact states**, and **State-driven requeueing** sections below for the
shared queue lanes, priority signals, state attributes, and follow-up task policy
that every worker should use when it emits more work.

## Uploaded-Content Review Prioritization

After hierarchical chunking, workers should rank sections for immediate review:

- dated claims
- numeric thresholds
- owner/person claims
- legal/regulatory statements
- future-looking or ambiguous language
- uncited operational claims
- claims contradicted by higher-authority sources
- sections that changed since last sync
- sections frequently retrieved by agents

Output:

```json
{
  "capability": "context.fragile_section.rank",
  "sections": [
    {
      "chunk_id": "chunk-...",
      "priority": "high",
      "signals": ["dated", "numeric", "legal"],
      "recommended_worker": "verify.statute.lookup",
      "reason": "dated numeric legal threshold needs current authority"
    }
  ]
}
```

## Kubernetes Image Pattern

Use a few lane-based images, not one image per task:

- `baltor-worker-cpu`: registry runner, deterministic workers.
- `baltor-worker-orchestrator`: fan-out/fan-in, N-pass coordination, package
  builds, low-dependency workflow glue.
- `baltor-worker-audit`: source trust, adversarial validation, injection
  screening, adoption policy checks.
- `baltor-worker-research`: search, browser fetch, website reading, source
  snapshots, archive submission.
- `baltor-worker-browser`: Playwright/browser tooling, strict sandbox when the
  research image needs full browser automation.
- `baltor-worker-ocr`: OCR/layout/document dependencies.
- `baltor-worker-ml`: local model clients, embedding/rerank dependencies.
- `baltor-worker-gpu`: high-throughput local model serving where available.

Each image starts the same entrypoint:

```bash
python -m scripts.context_workers.runner --watch
```

Capabilities are selected by task envelope and worker registration, not by
changing orchestration code.

The worker manifest should expose `capabilities`, `task_types`, `image`, and
`output_contract` so the router can place work into the cheapest safe pool. See
the **Recommended pools**, **Managed-service replacements for K8s**, and
**Orchestration shape and engine fit** sections below for the recommended split
between managed cloud services, always-on orchestrators, KEDA-scaled K8s pools,
and optional GPU workers.

## Python Code Organization

Start as a monorepo package with a plugin-style worker registry. Split into
private PyPI packages only after the contracts stabilize or dependencies diverge.

Current local structure:

```text
_repos/shared-backend-components/scripts/context_workers/
  registry.py              # task/worker/result contracts
  runner.py                # queue drain/watch/inline execution
  priority.py              # queue priority and follow-up policy
  common.py                # deterministic shared helpers
  tasks.py                 # compatibility import shell
  workers/
    chunk.py
    keyword.py
    entity.py
    claim.py
    graph.py
    fragility.py
    refresh.py
    pipeline.py
  backends/
    celery_app.py
    temporal_bridge.py
```

Future package split:

- `baltor-worker-core`: contracts, registry, runtime, telemetry, preflight,
  queues, artifact storage, shutdown handling.
- `baltor-worker-docs`: parsing, OCR, layout, tables, chunking.
- `baltor-worker-research`: browser/search/source-trust/archive capture.
- `baltor-worker-graph`: graph extraction, repair, indexing.
- `baltor-worker-models`: embeddings, rerankers, small-model and frontier-model
  adapters.

The stable extension point should be the task envelope, worker lifecycle, and
result contract, not a particular queue framework.

## Worker Lifecycle Hooks

Every worker should eventually support:

- `preflight`: check env vars, secrets, tools, model availability, network
  policy, allowlists, storage, and cost limits.
- `load`: lazily load models, browser contexts, index handles, or parser state.
- `execute`: run the task under deadline, retry, cost, and tenant-scope limits.
- `write_artifacts`: store raw outputs, evidence packets, graph records, and
  package manifests by content hash.
- `emit_followups`: enqueue child tasks with inherited state, priority signals,
  and queue policy.
- `shutdown`: release leases, close browser/model handles, flush telemetry, and
  clean temporary files.

That lifecycle keeps local SQLite workers, Redis/KEDA workers, Celery tasks,
Temporal activities, and Argo containers aligned.

## Safety And Governance

External workers must enforce domain allowlists, robots/rate limits where
applicable, max pages, max time, max cost, tenant-scoped caches, evidence
capture without excessive copied text, reproducible timestamps and source
hashes, and explicit unresolved status instead of guessed answers.

## Promotion Rule

A worker output can feed agent context only when it has source or internal
authority, requester scope allows it, freshness metadata exists, volatile claims
have a refresh policy, provenance is retained, and unresolved cases are not
silently promoted.

---

> **Consolidated model.** The sections below fold in the former
> `baltor-worker-operating-model.md`, `baltor-queue-priority-orchestration.md`, and
> `baltor-worker-orchestration-research.md` (a 2026-05-31 research note) — now archived under
> `_repos/_shared/archive/legacy/baltor/context/` for lineage. They are the shared operating model,
> queue/orchestration contract, and backend-tooling research for the worker fleet; the 18-bucket
> classification lives separately in `baltor-worker-taxonomy-and-buckets.md`.

## Platform shape and execution model

Baltor should use Kubernetes where control, isolation, dependency weight, GPU placement, or long-running
batch orchestration matter, and managed cloud services where the capability is commodity infrastructure:
queues, databases, object storage, transactional email, schedules, secrets, and small bursty functions.

```text
managed service first for commodity state and triggers
K8s worker pool for controlled execution
GPU pool only for workloads that materially benefit from local models
```

Use one worker contract and multiple execution substrates; no single backend defines the product model:

```text
task envelope
  -> worker registry
  -> queue/orchestrator adapter
  -> managed function, Cloud Run job, K8s deployment, Argo step, or Temporal activity
  -> artifact/evidence store
  -> state transition and follow-up tasks
```

The stable product model is the task envelope, lifecycle hooks, artifact contracts, fact/source state, and
priority policy — not a particular queue framework.

## Worker runtime contract

Every worker image should expose the same entrypoint and lifecycle: receive task envelope → preflight →
load → execute → write artifacts → emit follow-up tasks → shutdown.

The Python runner enforces this contract around every registered worker. `_repos/shared-backend-components/scripts/context_workers/lifecycle.py`
emits structured JSON lifecycle events, adds runtime metadata to each ledger row, and records
preflight/load/execute/follow-up/closeout stages. `_repos/shared-backend-components/scripts/context_workers/runner.py` traps `SIGTERM` and
`SIGINT` so container workers finish the current claimed task or exit their poll loop cleanly.
`_repos/shared-backend-components/scripts/context_workers/runtime_io.py` is the shared runtime substrate: atomic JSON writes, artifact
manifests, heartbeat/status files, runtime health checks, and idempotency markers. Completed work suppresses
duplicate delivery; held or failed work can be resumed after an explicit operator action.

The code contract is carried by the registry metadata:

- `name`: stable worker id.
- `lane`: queue lane.
- `capabilities`: what the worker can do.
- `task_types`: task intents it can satisfy.
- `image`: preferred image class.
- `output_contract`: result artifact contract.
- `max_retries`: retry budget.
- `idempotent`: whether the task can be retried safely.
- `cost_policy`: whether the worker emits cost estimates, needs a budget ceiling, should batch by default,
  and which resources it meters.

This lets the same worker run locally, in Celery, as a Temporal activity, as an Argo step, or in a
KEDA-scaled K8s deployment without changing business logic. The portable JSON form is defined in
`_repos/shared-backend-components/schemas/worker-manifest.schema.json`, and the deterministic router lives in `_repos/shared-backend-components/scripts/context_workers/router.py`.

## Recommended pools

| Pool | Runtime | Runs | Scaling | Notes |
|---|---|---|---|---|
| API | Cloud Run, Fly.io, Render, or K8s deployment | user/API traffic | request autoscale | Keep stateless. |
| Orchestrator | Temporal workers or small K8s deployment | durable syncs, adoption flows, fan-out/fan-in | always-on 2 replicas in prod | Owns customer-visible progress. |
| CPU worker | KEDA-scaled K8s deployment or Cloud Run Jobs | chunking, claims, entity, graph, packaging | scale to zero in dev/small prod | Default pool. |
| Audit worker | K8s deployment with stricter policy | adversarial checks, source trust, injection screening | small min replica or scheduled | Treat as security-sensitive. |
| Browser/research worker | K8s deployment or cloud function with browser support | site search, price checks, statute reads, source snapshots | queue depth and rate-limit aware | Strong egress and domain controls. |
| OCR/doc worker | K8s job/deployment | OCR, layout, tables, PDF parsing | batch scale | Heavy native deps justify a separate image. |
| GPU worker | K8s GPU node pool, RunPod, Modal, or managed endpoint | embeddings, rerankers, small open models | scale by queue and GPU availability | Keep optional; API model lane remains fallback. |
| Archive worker | cloud function or K8s CPU worker | archive.org submission, content hash capture | low concurrency | Isolate from critical path. |

Every pool must understand `cost_estimate` and `budget_policy` from the task envelope. Research, browser,
audit, and GPU workers should default to explicit budget ceilings and tenant-level concurrency caps.
Nonurgent expensive tasks should be routed to batch/flex processing where possible.

## Orchestration options and worker-pool research

Managed services should be the default for Postgres/pgvector, object storage, queue primitives, secrets,
transactional email, schedules, observability, and simple event functions. K8s should be used when Baltor
needs Playwright/browser isolation, OCR/native dependency control, GPU node placement, tenant-specific
network policy, long-running queue drainers, batch DAGs over large corpora, or custom image/resource profiles.

| Option | Best use | Avoid when | Baltor role |
|---|---|---|---|
| Local SQLite/Redis runner | local dev, CI, demos | production durability is needed | default local parity |
| Cloud Tasks / SQS / Pub/Sub | simple queues, rate limits, retries | complex multi-step stateful workflows are needed | managed queue option |
| Cloud Run Jobs / Azure Container Apps Jobs | finite container tasks with autoscaling | heavy browser/GPU/sandbox control is needed | bursty stateless execution |
| Lambda / Cloud Functions | small event-driven tasks | long jobs, heavy dependencies, browser automation | source pings, webhooks, archive callbacks |
| KEDA + K8s deployments | queue-draining worker pools, scale-to-zero | team cannot operate K8s yet | main controlled worker fleet |
| Argo Workflows | large bounded container DAGs | workflows span days or require human gates | reindex, rebuild, OCR batches |
| Temporal | durable workflows, retries, heartbeats, resumability | trivial fire-and-forget tasks | source sync, adoption, customer-visible progress |
| Celery | Python-native task routing and inspection | strict durability/replay is required | optional early backend, not source of truth |

Research-view pool design (image class per workload): CPU (`baltor-worker-cpu`, cheap default — chunking,
keyword, claims, graph, package exports); Orchestrator (`baltor-worker-orchestrator`, small and reliable —
fan-out/fan-in, progress, N-pass); Audit (`baltor-worker-audit`, stricter egress/logging — adversarial
validation, injection screening, trust scoring); Research (`baltor-worker-research`, domain allowlists +
source snapshots — search, source lookup, official page reads); Browser (`baltor-worker-browser`, Playwright
sandbox — JS-heavy pages, price checks, dynamic sites); OCR/doc (`baltor-worker-ocr` — PDFs, scans, tables,
layout); GPU (`baltor-worker-gpu`, optional with API fallback — embeddings, rerankers, local small models);
Archive (`baltor-worker-archive` or function, low concurrency — archive submissions and hash capture).

Docs: KEDA external-scaler model <https://keda.sh/docs/2.19/concepts/external-scalers/>, Argo Workflows
<https://argoproj.github.io/workflows/>, Temporal <https://docs.temporal.io/> and Python SDK
<https://python.temporal.io/>, Celery routing <https://docs.celeryq.dev/en/latest/userguide/routing.html>,
Cloud Run <https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run>, Cloud Tasks
<https://docs.cloud.google.com/tasks/docs/configuring-queues>, AWS Lambda + SQS
<https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html>, Azure Container Apps jobs
<https://learn.microsoft.com/en-us/azure/container-apps/jobs>, AWS Step Functions
<https://aws.amazon.com/documentation-overview/step-functions/>.

## Queue lanes

Every source, fact, graph edge, label, and model-derived finding can create follow-up work. The core
contract is:

```text
finding -> state transition -> priority policy -> research task -> worker lane -> evidence -> next transition
```

Use lanes for work class, not product feature:

| Lane | Runs |
|---|---|
| `ingest` | upload intake, connector snapshots, source metadata |
| `normalize` | OCR, HTML/PDF conversion, chunking |
| `analyze` | keywords, entities, claims, dates, numeric facts |
| `graph` | nodes, edges, source graphs, claim graphs |
| `embed` | vector records for chunks, claims, entities |
| `verify` | source agreement, precedence, scope/date checks |
| `refresh` | scheduled rechecks and CDC-driven updates |
| `research` | web/site search, official-source lookup, price/address/statute tasks |
| `archive` | archive capture and content-hash preservation |
| `promote` | context-pack update, index publish, serving package generation |
| `review` | rare human or adversarial review when workers cannot resolve |
| `orchestrate` | fan-out/fan-in and N-pass run coordination |

Each lane can run on the same local SQLite queue during development. In cloud, each lane maps to a queue key
and KEDA-scaled worker pool.

## Shared state model and fact states

Published catalog components keep the public `lifecycle` field: `experimental`, `beta`, `stable`,
`deprecated`. Operational objects use richer states from `_repos/shared-backend-components/schemas/_common.schema.json`: `source-record`,
`fact-record`, `normalized-object-record`, `entity-record`, `label-record`, `dimension-record`,
`review-ticket`, `object-factory-job`, `research-task`, `capability-request`. Every operational object can
carry `state`, `state_history`, `priority`, `priority_signals`, and `queue_policy`.

Facts additionally carry `fact_state` (or `state` in `fact-record`) so Baltor can distinguish: candidate
found in upload; one source found; two independent sources found; authoritative source found; needs second
source; needs reconciliation; needs trust review; ready for adoption; served current; superseded or rejected.
This gives the system memory — a useful one-source fact found yesterday is a scheduled follow-up, not a dead
end.

## Queue states (operator language)

Queue states should use explicit product and operator language that says *why* a task is not running; avoid
vague broker terms in product copy and operational docs.

| State | Meaning | Default action |
|---|---|---|
| `pending` | Ready for a worker to claim. | KEDA scales on this queue. |
| `processing` | Claimed by a worker. | Lease, heartbeat, or retry if stalled. |
| `approval_required` | Valid task, but budget or policy requires approval before execution. | Hold and show in UI; do not run automatically. |
| `budget_blocked` | Valid task, but tenant/task budget is insufficient. | Hold as blocked until budget or policy changes. |
| `failed_permanently` | Malformed, unsupported, or repeatedly failing task after retry budget. | Inspect, fix producer or worker, then requeue if appropriate. |

Local and cloud-equivalent operators expose the same actions; approving a job does not erase its history —
the requeued task carries `requeued_from_status`, `requeued_at`, and explicit override metadata:

```bash
python -m scripts.context_workers.runner --queue-stats
python -m scripts.context_workers.runner --queue-list approval_required
python -m scripts.context_workers.runner --preflight-task task.json
python -m scripts.context_workers.runner --approve-job cw_...
python -m scripts.context_workers.runner --requeue-budget-blocked-job cw_...
python -m scripts.context_workers.runner --requeue-failed-job cw_...
```

## Priority signals and default policy

Priority should be explainable. A queued task stores raw signals plus the resolved policy decision.

Core signals: `risk` (legal/compliance/safety/financial/customer-harm), `customer_impact`, `agent_usage`,
`source_authority`, `source_count`, `freshness_age_hours`, `failed_attempts`, `deadline_hours`,
`injection_risk`, `manual_review_cost`. The priority policy resolves: `lane`, `priority`, `priority_score`,
`reason_codes`, `not_before`, `deadline_at`, `max_attempts`, `backoff`, `dedupe_key`, `cost_estimate`,
`budget_policy`. Users should rarely double-check facts; manual review is a terminal fallback after cheaper
deterministic, search, and Hermes/OpenClaw workers have failed or found genuine ambiguity.

Initial deterministic policy:

| Finding | Next task | Lane | Priority rule |
|---|---|---|---|
| extracted candidate with no sources | `verify.official_source.find` | `research` | normal, high if risky |
| one source found | `verify.second_source.find` | `research` | high if risky, used by agents, or older than a day |
| two independent sources found | `source.archive.submit` | `archive` | normal unless high impact |
| authoritative source found | `source.archive.submit` | `archive` | normal; can skip second-source requirement |
| source disagreement | `context.reconcile.claims` | `verify` | high |
| possible spam/injection | `openclaw.adversarial.review` | `review` | blocked/high until resolved |
| repeated search failures | `hermes.procedure.discover` | `research` | high if fact still matters |
| volatile served fact aging out | `verify.official_source.find` | `refresh` | based on refresh SLA |
| adopted high-impact fact | `source.archive.submit` | `archive` | high |

## Budget and cost policy

Every queued task carries a planning estimate, even a small one, keeping local dev, KEDA workers, Temporal
activities, Argo batch jobs, and future hosted billing aligned around one task envelope. Shared fields:
`cost_estimate` (estimated total, floor, ceiling, search calls, browser seconds, worker seconds, GPU seconds,
line items) and `budget_policy` (tenant budget remaining, task ceiling, monthly ceiling, budget-used percent,
action, reason codes).

| Action | Meaning |
|---|---|
| `allow` | enqueue immediately |
| `batch` | enqueue, but prefer async/batch processing when latency allows |
| `require_approval` | route to `approval_required` until tenant/admin approval or an explicit budget override exists |
| `block` | route to `budget_blocked` because the remaining tenant budget is insufficient |

The default helper in `_repos/shared-backend-components/scripts/context_workers/priority.py` estimates each research task from its `task_type`,
priority, failed attempts, and usage signals. The estimate is an orchestration guardrail, not a customer
invoice — it prevents a rare hard case from silently becoming an unbounded model, browser, or GPU bill.
Production routers should enforce lane-level concurrency caps for `research`/`review`/`browser`/`gpu`, tenant
monthly ceilings, per-task ceilings for Hermes/OpenClaw/frontier lanes, batch routing for nonurgent expensive
work, and ledgered overrides for any approval-required task. Do not mix `failed_permanently` with
`approval_required` or `budget_blocked`; each state answers a different operator question.

## Task routing rules

Workers route by task intent, capability, policy, and cost — not by implementation detail:

```text
task_type + source_scope + model_policy + priority
  -> worker capability match
  -> image class
  -> queue lane
  -> execution backend
```

The router stays simple and explainable. It scores: explicit worker id; exact task-type support; requested
lane; requested image; high injection risk requiring audit placement; research tasks preferring
research/browser pools; GPU model policies preferring GPU workers when registered.

| Task | Preferred first route | Escalation route |
|---|---|---|
| `document.chunk` | CPU worker | none |
| `entity.extract` | CPU worker with rules/spaCy/GLiNER | model API worker for ambiguous domains |
| `web.price.check` | browser/research worker | Hermes worker if page flow is unknown |
| `web.statute.read` | browser/research worker with official-source policy | audit worker for scope disputes |
| `web.business.hierarchy.find` | research worker + graph worker | frontier model summarizer with deterministic artifact output |
| `verify.second_source.find` | research worker | Hermes procedure discovery after repeated failures |
| `source.trust.score` | audit worker | OpenClaw adversarial review |
| `package.rag.build` | CPU worker | none |
| `embed.claims` | GPU worker or managed embedding API | queue until GPU available if data cannot leave tenant scope |

## State-driven requeueing

Every run scans active records for requeue triggers: `one_source_found` older than 24h → second-source
search; `needs_second_source` with high agent usage → urgent second-source search; `needs_reconciliation` →
verify lane; `needs_trust_review` → adversarial review; `needs_archive_capture` → archive lane;
`served_current` with stale freshness SLA → refresh lane; `failed` with retryable reason → backoff retry;
`failed` after max attempts → Hermes/OpenClaw or rare review; `superseded` → graph/index propagation. The
requeue process dedupes by `(tenant_id, task_type, fact_id, source_id, target_url)` so repeated agent requests
raise priority without flooding the queue; the deterministic helper emits this as `queue_policy.dedupe_key`.

## Research task examples

Standardized task types share one envelope and differ only by payload and worker capability:
`web.price.check`, `web.statute.read`, `web.site.search`, `web.business.address.find`,
`web.business.hierarchy.find`, `web.news.mna.scan`, `docs.capability.lookup`, `verify.second_source.find`,
`verify.official_source.find`, `source.trust.score`, `source.archive.submit`. This is how Baltor adds new
research skills without creating a new orchestration system each time.

## Managed-service replacements for K8s

Use managed services where they reduce operational drag without weakening the control plane.

| Need | Preferred managed option | K8s alternative | Decision rule |
|---|---|---|---|
| Queue | SQS, Pub/Sub, Cloud Tasks, Upstash Redis, managed RabbitMQ | Redis/RabbitMQ in cluster | Managed unless local broker semantics are required. |
| Database | managed Postgres + pgvector | Postgres operator | Managed for production unless data residency requires otherwise. |
| Object storage | S3, GCS, R2, Azure Blob | MinIO | Managed in cloud, MinIO locally. |
| Search/index | OpenSearch Serverless, Meilisearch Cloud, Algolia, managed Elasticsearch | OpenSearch in cluster | Managed until scale/control needs justify ops. |
| Scheduling | cloud scheduler, Temporal schedules | CronJob | Managed for simple schedules; Temporal for durable customer workflows. |
| Small bursty task | Cloud Run Job, Lambda, Cloud Functions | K8s Job | Managed when cold start and limits are acceptable. |
| Transactional email | Resend, Postmark, SES, SendGrid | none | Always managed. |
| Secrets | cloud secrets manager | External Secrets Operator | Managed source of truth. |
| Observability | hosted OpenTelemetry/Grafana/Datadog | Prometheus/Grafana in cluster | Hosted first unless cost/control pushes in-cluster. |

## Orchestration shape and engine fit

Local: `SQLite queue -> scripts.context_workers.runner -> JSONL ledger`.

Cloud:

```text
API / scheduler
  -> queue router
  -> Redis/SQS/PubSub/Cloud Tasks lane queues
  -> KEDA worker pools
  -> Postgres + object storage + vector store
  -> Temporal workflow state for resumable customer-visible runs
  -> Argo for large bounded DAG batches
```

KEDA fits lane queues (scales from external event sources, scale-to-zero). Argo Workflows fits container-native
parallel jobs. Temporal fits durable workflows with activity retries, heartbeats, and customer-visible
resumability — it should own connector sync, source diff, multi-day second-source search, approval-free
adoption when policies pass, rare review gates, and serving-package generation. Argo should own bounded batch
DAGs — rebuild a tenant graph, re-OCR a corpus, re-embed all claims, run an N-pass reindex. Celery is a useful
adapter for Python task ergonomics but should not define the product contract (the contract is the task
envelope, state history, and priority policy).

## Document processing research

Prefer deterministic or local-first document processing before model escalation.

| Need | Candidate tools | Notes |
|---|---|---|
| PDF/DOCX/HTML conversion | Docling, Unstructured, PyMuPDF | Docling emphasizes structured conversion, OCR, tables, formulas, reading order. Unstructured partitions documents into semantic elements before chunking. |
| Chunking | structure-aware chunks, LangChain splitters, LlamaIndex ingestion | LangChain recommends recursive splitting as a generic baseline. LlamaIndex ingestion pipelines hash/cache node + transformation pairs. |
| Entity extraction | spaCy, GLiNER | spaCy has mature production pipelines; GLiNER is useful for lightweight zero-shot entity types. |
| Graph extraction | NetworkX, Neo4j GraphRAG, docling-graph | Use deterministic entity/claim edges first; escalate to LLM relation extraction when needed. |
| Hybrid retrieval | pgvector, BM25, graph traversal, rerankers | Serve text, RAG, graph, and audit packages from the same evidence lineage. |

Docs: Docling <https://www.docling.ai/>, Unstructured chunking
<https://docs.unstructured.io/open-source/core-functionality/chunking>, LangChain splitters
<https://docs.langchain.com/oss/python/integrations/splitters/index>, LlamaIndex ingestion
<https://docs.llamaindex.ai/en/stable/module_guides/loading/ingestion_pipeline/>, spaCy
<https://spacy.io/usage/processing-pipelines/>, GLiNER <https://github.com/urchade/GLiNER>, Neo4j GraphRAG
<https://neo4j.com/labs/genai-ecosystem/graphrag/>. PyMuPDF/PyMuPDF4LLM emit LLM/RAG-friendly Markdown with
tables in reading order <https://github.com/pymupdf/PyMuPDF>; Surya covers OCR, layout, reading order, and
table recognition <https://github.com/datalab-to/surya>; Scrapy is the mature Python crawling framework
<https://github.com/scrapy/scrapy>.

## Reusable project and package map

Baltor standardizes around wrappers and artifact contracts, not private forks of every document, crawler,
model, and orchestration project. The worker contract is the stable surface; packages underneath change per
workload, tenant, file type, or deployment environment.

| Domain | Projects to evaluate | How Baltor should use them |
|---|---|---|
| PDF/page extraction | PyMuPDF, PyMuPDF4LLM, pdfplumber, Poppler | Page splitting/rendering, bounding boxes, first-pass text/table extraction. Wrap as `document.page.extract` and `document.page.render`. |
| Structured document conversion | Docling, Unstructured, MinerU | Convert PDFs/DOCX/HTML/images into page/component trees. Use as pluggable `document.structure.extract` backends. |
| OCR/layout/tables | Surya, PaddleOCR, EasyOCR, Tesseract, LayoutParser, Camelot/Tabula-style table tools | Run in OCR/doc image. Emit page components with coordinates and confidence. |
| Web crawling | Scrapy, scrapyd, trafilatura, inscriptis, Playwright | Scrapy for broad crawls; trafilatura/inscriptis for clean article text; Playwright only for dynamic/workflow-heavy pages. |
| Browser agents | Playwright, browser-use, hosted browser APIs where allowed | Keep behind `baltor-worker-browser`; require domain allowlists, egress policy, source snapshots, injection checks. |
| Model gateway | LiteLLM, Portkey Gateway, OpenRouter, direct OpenAI-compatible client | Use under Baltor's policy resolver. Do not let the gateway decide privacy, adoption, or source-trust policy. |
| Orchestration | Temporal, Argo Workflows, Prefect, Dagster, Celery, KEDA | Temporal for durable customer-visible flows; Argo for large K8s batch DAGs; Celery/Redis for early local/Python async; Prefect/Dagster where teams already use them. |
| Graph extraction | NetworkX, Neo4j GraphRAG, DeepKE, graph_builder, Open Semantic ETL | Start deterministic; use relation-extraction packages for candidate edges, not direct fact adoption. |
| Observability/evals | OpenTelemetry, Langfuse, promptfoo, Ragas, DeepEval | Emit traces + model-route records for every model call; use eval packages to regression-test extraction, RAG, reconciliation, distillation. |
| Provenance/archive | Internet Archive Save Page Now, wayback Python clients, WARC tooling | Archive high-value verification sources; store hashes, timestamps, URL, retrieval method, source-state transitions. |

Portkey Gateway/LiteLLM cover multi-provider routing/fallback and OpenRouter offers hosted provider
ordering/fallback: <https://github.com/Portkey-ai/gateway>, <https://docs.litellm.ai/>,
<https://openrouter.ai/docs/features/provider-routing>. Langfuse gives open-source LLM observability with
OpenTelemetry integration: <https://github.com/langfuse/langfuse>.

## Standardization strategy

Use a three-layer package strategy so external tools cannot leak into fact records, serving packages, queue
payloads, or customer-visible exports (store native metadata in `raw_backend_metadata` only when useful for
debugging):

```text
1. Baltor artifact contracts
   stable JSON schemas for pages, components, chunks, claims, facts, routes,
   source snapshots, evidence packets, and serving packages
2. Baltor worker adapters
   small wrappers that call Docling, PyMuPDF, Surya, Scrapy, LiteLLM, Temporal, Langfuse, etc.
   and normalize outputs into Baltor contracts
3. External packages/images
   version-pinned dependencies isolated by image class: CPU, OCR/doc, browser, GPU, audit, research, orchestrator
```

The CPU worker should not carry browser dependencies, OCR models, or GPU runtimes; the OCR/doc worker should
not know adoption policy; the model gateway should not know whether a fact is safe to serve. Adoption rule for
every external project: **wrap, normalize, test, and trace**.

| Need | Package shape | Reason |
|---|---|---|
| Shared contracts | internal Python package, later private/public PyPI | Every worker imports the same envelope, lifecycle, and schema helpers. |
| Worker adapters | repo modules first, split into packages when stable | Avoid premature packaging while APIs are still changing. |
| Heavy document tools | separate container images | Keep CPU workers small and reduce local setup pain. |
| Browser/research | isolated image or managed browser service | Stronger sandboxing and egress control. |
| Model gateway | thin internal resolver plus optional LiteLLM/Portkey/OpenRouter backend | Baltor keeps privacy/budget policy; gateway handles provider mechanics. |
| Evals/distillation | dataset artifacts plus eval runners | Frontier outputs become replay fixtures and fine-tuning candidates. |

## Model hierarchy

Use models as a costed escalation ladder:

| Stage | Tooling | Role |
|---|---|---|
| deterministic | regex, parsers, metadata, rules | first pass, cheap and reproducible |
| local small model | spaCy/GLiNER/rerankers/Gemma-class models | entity, classification, summaries, rerank |
| local GPU/open model | vLLM/Ollama workers | higher-volume private processing |
| hosted frontier model | API model | hard reconciliation, summaries, source comparison |
| Hermes/OpenClaw | open-ended and adversarial workers | unresolved cases and procedure discovery |
| compiled rule | deterministic worker/template | future cheap replay |

The key product loop: expensive non-deterministic discovery → evidence packet → deterministic
resolver/template → replay fixture → cheaper future worker run.

## Hermes and OpenClaw rule

Hermes and OpenClaw workers may use open-ended model reasoning, but their durable output is not just a fact.
It should be: an evidence packet; a source list; a state-transition recommendation; a deterministic resolver
rule when possible; an extraction/query template when possible; confidence and unresolved scope; and a replay
test fixture. The goal is to pay for non-deterministic reasoning once, then compile the useful part into a
cheaper deterministic worker, rule, template, or priority policy.

## Adversarial validation checklist

Before promoting a worker or pool to production, validate these failure modes:

| Risk | Test | Required behavior |
|---|---|---|
| Duplicate delivery | run same task twice with same idempotency key | one durable artifact set, no duplicate adopted fact |
| Malformed or unsupported task | malformed payload, unsupported source, bad file | task fails with structured error and `failed_permanently` after retry budget |
| Network stall | website hangs or rate-limits | timeout, retry/backoff, no stuck lease |
| Source injection | page contains prompt-injection or spam text | evidence captured, adoption blocked, trust task emitted |
| Source drift | source content changes between fetch and parse | version/hash mismatch recorded and requeue created |
| Partial model output | LLM returns invalid JSON or vague answer | no adoption; deterministic retry or Hermes/OpenClaw follow-up |
| Single-source claim | one plausible source found | state is `one_source_found`; second-source task scheduled |
| High-authority source | official source found | archive task scheduled; second source can be policy-skipped |
| Browser sandbox escape | page downloads files or redirects | domain/egress policy blocks unexpected behavior |
| GPU unavailable | local model pool empty | route to API model or queue with SLA-aware priority |
| Queue flood | same fact requested repeatedly | dedupe key raises priority without creating unbounded tasks |
| Shutdown during task | pod termination or function timeout | heartbeat/lease allows retry from last durable state |

## Reliability practices

Workers are designed for at-least-once execution: idempotency key per task and artifact; content hashes for
inputs and outputs; leases and heartbeats for long-running tasks; explicit max attempts plus specific
terminal/hold states (`approval_required`, `budget_blocked`, `failed_permanently`); structured failure
reasons; queue dedupe key by tenant, task type, fact id, source id, and URL; retry with backoff; no adoption
from failed/partial/malformed outputs; deterministic replay fixtures for model-discovered procedures; and
OpenTelemetry traces, metrics, and logs around every task. For source refresh, state history is
product-critical (`candidate_detected → one_source_found → needs_second_source → two_sources_found → archived
→ ready_for_adoption → served_current`) — a one-source finding schedules a higher-priority second-source
search rather than being discarded.

## Source trust and security research

External-source workers are exposed to untrusted content; assume web pages, PDFs, emails, and retrieved
snippets can carry malicious instructions or spam. Controls: separate instructions from source text in every
prompt; never let source text select tools or permissions; enforce domain allowlists, egress limits, and
source-scope policies; capture source URL, retrieval timestamp, content hash, and evidence span; require
source trust scoring before adoption; retain original customer-source claim and new verified fact in
provenance; prefer official/primary sources for adoption; require two independent sources unless policy allows
an authoritative source; archive important sources after verification; keep unresolved states instead of
guessing. Docs: OWASP LLM Prompt Injection Prevention
<https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html>, OWASP
Prompt Injection <https://owasp.org/www-community/attacks/PromptInjection>, NIST AI RMF
<https://www.nist.gov/itl/ai-risk-management-framework>, OpenTelemetry <https://opentelemetry.io/docs/>,
Internet Archive Save Page Now <https://wiki.archiveteam.org/index.php/Internet_Archive/Save_Page_Now>.

## Always-on components

In production keep available: API service; database; object storage; queue service; Temporal service or cloud
equivalent for durable workflows; at least two orchestrator workers per critical task queue; observability
collector; minimal audit/research capacity for urgent trust issues. Everything else can scale to zero when the
queue is empty if startup latency is acceptable.

## Local development shape and production shape

Local should remain boring, and use the same task envelope, worker registry, and result contracts as cloud
(local runners may skip managed auth and use synthetic connectors, but not a different business workflow):

```text
Docker Compose
  Postgres + pgvector
  Redis or SQLite queue
  MinIO
  optional Ollama/vLLM
  worker runner
  showcase/admin API
```

Production:

```text
Cloudflare/Vercel frontend
FastAPI or equivalent API
managed Postgres + pgvector
managed object storage
managed queue
Temporal for durable workflows
KEDA-scaled K8s worker pools
Argo for large batch corpus workflows
managed email/secrets/observability
optional GPU pool or hosted model endpoints
```

This keeps Baltor flexible: simple tenants run on managed services and CPU workers; regulated or high-scale
tenants move execution into isolated K8s pools with GPU and browser sandboxes.

## Implementation hooks and next steps

Current hooks: shared schema defs in `_repos/shared-backend-components/schemas/_common.schema.json`; operational schemas for facts, research
tasks, source records, jobs, entities, labels, dimensions, reviews, normalized objects; deterministic policy
in `_repos/shared-backend-components/scripts/context_workers/priority.py`; worker follow-up emission in `_repos/shared-backend-components/scripts/context_workers/tasks.py`;
lifecycle requeue scanning in `_repos/shared-backend-components/scripts/context_workers/requeue.py`; task cost/budget helpers in
`_repos/shared-backend-components/scripts/context_workers/priority.py`; adversarial routing/requeue fixtures in
`_repos/shared-backend-components/scripts/context_workers/adversarial_fixtures.py`. Run:

```bash
python -m scripts.context_workers.runner --adversarial-fixtures
python -m scripts.context_workers.runner --requeue-scan facts-and-sources.json
```

Implemented follow-up: `_repos/shared-backend-components/schemas/worker-manifest.schema.json` defines the portable worker manifest;
`_repos/shared-backend-components/scripts/context_workers/router.py` maps task envelopes to registered workers, lanes, image classes, output
contracts, and reason codes; `_repos/shared-backend-components/scripts/context_workers/requeue.py` scans active fact/source records and emits
deduped follow-up tasks for one-source, stale, reconciliation, source-trust, and archive-capture cases;
`_repos/shared-backend-components/scripts/context_workers/adversarial_fixtures.py` covers prompt injection, duplicate follow-ups, scanner
dedupe, source-trust blocking, archive routing, and single-source follow-up policy.

Next steps: persist fact records and research tasks in Postgres; add lane-specific queue keys as shared
constants; promote the lifecycle scanner into a scheduled local/Temporal/KEDA job once fact records persist;
add worker dashboards for queue depth, oldest task, ETA, retry count, and blocked tasks; add Temporal
workflows for source sync and fact adoption; add Argo templates for corpus-scale batch runs; add a
managed-service deployment matrix for AWS/GCP/Azure/local; add OpenTelemetry task spans around `process_one`;
add optional Docling/Unstructured/GLiNER workers behind dependency groups, not hard base dependencies.

## Product implications

Demo and GTM language should emphasize automated verification and refresh; reconciled and traceable context;
source lineage and adoption states; rare manual exceptions; serving packages for text, RAG, graph, and audit;
and local-first execution with cloud-scale worker pools. Avoid positioning Baltor as another generic agent
builder. The stronger claim: **Baltor keeps enterprise agent context verified, current, traceable, and ready
to serve.**
