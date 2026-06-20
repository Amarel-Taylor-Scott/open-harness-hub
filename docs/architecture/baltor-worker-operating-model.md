# Baltor Worker Operating Model

Baltor should use Kubernetes where control, isolation, dependency weight, GPU
placement, or long-running batch orchestration matter. It should use managed
cloud services where the capability is commodity infrastructure: queues,
databases, object storage, transactional email, schedules, secrets, and small
bursty functions.

The rule is:

```text
managed service first for commodity state and triggers
K8s worker pool for controlled execution
GPU pool only for workloads that materially benefit from local models
```

## Worker Runtime Contract

Every worker image should expose the same entrypoint and lifecycle:

```text
receive task envelope
preflight
load
execute
write artifacts
emit follow-up tasks
shutdown
```

The Python runner now enforces this contract around every registered worker.
`scripts/context_workers/lifecycle.py` emits structured JSON lifecycle events,
adds runtime metadata to each ledger row, and records preflight/load/execute/
follow-up/closeout stages. `scripts/context_workers/runner.py` also traps
`SIGTERM` and `SIGINT` so container workers can finish the current claimed task
or exit their poll loop cleanly.

`scripts/context_workers/runtime_io.py` is the shared runtime substrate. It owns
atomic JSON writes, artifact manifests, heartbeat/status files, runtime health
checks, and idempotency markers. Completed work suppresses duplicate delivery;
held or failed work can be resumed after an explicit operator action.

The code contract is carried by the registry metadata:

- `name`: stable worker id.
- `lane`: queue lane.
- `capabilities`: what the worker can do.
- `task_types`: task intents it can satisfy.
- `image`: preferred image class.
- `output_contract`: result artifact contract.
- `max_retries`: retry budget.
- `idempotent`: whether the task can be retried safely.
- `cost_policy`: whether the worker emits cost estimates, needs a budget
  ceiling, should batch by default, and which resources it meters.

This lets the same worker run locally, in Celery, as a Temporal activity, as an
Argo step, or in a KEDA-scaled K8s deployment without changing business logic.
The portable JSON form is defined in `schemas/worker-manifest.schema.json`, and
the deterministic router lives in `scripts/context_workers/router.py`.

## Recommended Pools

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

Every pool must understand `cost_estimate` and `budget_policy` from the task
envelope. Research, browser, audit, and GPU workers should default to explicit
budget ceilings and tenant-level concurrency caps. Nonurgent expensive tasks
should be routed to batch/flex processing where possible.

Queue states should use explicit product and operator language:

| State | Meaning | Default action |
|---|---|---|
| `pending` | Ready for a worker to claim. | KEDA scales on this queue. |
| `processing` | Claimed by a worker. | Lease, heartbeat, or retry if stalled. |
| `approval_required` | Valid task, but budget or policy requires approval before execution. | Hold and show in UI; do not run automatically. |
| `budget_blocked` | Valid task, but tenant/task budget is insufficient. | Hold as blocked until budget or policy changes. |
| `failed_permanently` | Malformed, unsupported, or repeatedly failing task after retry budget. | Inspect, fix producer or worker, then requeue if appropriate. |

Avoid vague broker terms in product copy and operational docs. The state should
say why the task is not running.

Local and cloud-equivalent operators should expose the same actions:

```bash
python -m scripts.context_workers.runner --queue-stats
python -m scripts.context_workers.runner --queue-list approval_required
python -m scripts.context_workers.runner --preflight-task task.json
python -m scripts.context_workers.runner --approve-job cw_...
python -m scripts.context_workers.runner --requeue-budget-blocked-job cw_...
python -m scripts.context_workers.runner --requeue-failed-job cw_...
```

Approving a job does not erase its history. The requeued task carries
`requeued_from_status`, `requeued_at`, and explicit override metadata so the
ledger can show who or what allowed the second execution attempt.

KEDA is a good fit for lane queues because it scales workloads from external
event sources and can scale deployments to zero. Argo Workflows is a good fit
for container-native parallel jobs on Kubernetes. Temporal is a good fit for
durable workflows, activity retries, heartbeats, and customer-visible
resumability. Celery remains useful for Python-native task routing when its
ecosystem is enough and durability requirements are modest.

Sources: KEDA <https://keda.sh/>, Argo Workflows
<https://argoproj.github.io/workflows/>, Temporal docs
<https://docs.temporal.io/>, Celery routing docs
<https://docs.celeryq.dev/en/latest/userguide/routing.html>.

## Managed-Service Replacements For K8s

Use managed services where they reduce operational drag without weakening the
control plane.

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

Local parity can still use Docker Compose with Redis, Postgres, MinIO, and the
same worker entrypoint.

## Adversarial Validation Checklist

Before promoting a worker or pool to production, validate these failure modes:

| Risk | Test | Required behavior |
|---|---|---|
| Duplicate delivery | run same task twice with same idempotency key | one durable artifact set, no duplicate adopted fact |
| Malformed or unsupported task | malformed payload, unsupported source, bad file | task fails with structured error and `failed_permanently` state after retry budget |
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

## Task Routing Rules

Workers should not route by implementation detail. They route by task intent,
capability, policy, and cost.

```text
task_type + source_scope + model_policy + priority
  -> worker capability match
  -> image class
  -> queue lane
  -> execution backend
```

The current router intentionally stays simple and explainable. It scores:

- explicit worker id;
- exact task-type support;
- requested lane;
- requested image;
- high injection risk requiring audit placement;
- research tasks preferring research/browser pools;
- GPU model policies preferring GPU workers when registered.

Examples:

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

## Hermes And OpenClaw Rule

Hermes and OpenClaw workers are allowed to use open-ended model reasoning, but
their output is not just a fact. Their durable output should be:

- evidence packet;
- source list;
- state transition recommendation;
- deterministic resolver rule when possible;
- extraction/query template when possible;
- confidence and unresolved scope;
- replay test fixture.

The goal is to pay for non-deterministic reasoning once, then compile the useful
part into a cheaper deterministic worker, rule, template, or priority policy.

## Always-On Components

In production, keep these available:

- API service;
- database;
- object storage;
- queue service;
- Temporal service or cloud equivalent for durable workflows;
- at least two orchestrator workers per critical task queue;
- observability collector;
- minimal audit/research capacity for urgent trust issues.

Everything else can scale to zero when the queue is empty if startup latency is
acceptable.

## Local Development Shape

Local should remain boring:

```text
Docker Compose
  Postgres + pgvector
  Redis or SQLite queue
  MinIO
  optional Ollama/vLLM
  worker runner
  showcase/admin API
```

The same task envelope, worker registry, and result contracts must run locally
and in cloud. Local runners can skip managed auth and use synthetic connectors,
but they should not use a different business workflow.

## Production Shape

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

This keeps Baltor flexible: simple tenants can run on managed services and CPU
workers; regulated or high-scale tenants can move execution into isolated K8s
pools with GPU and browser sandboxes.
