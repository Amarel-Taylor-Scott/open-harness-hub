# Baltor Queue Priority Orchestration

Baltor needs an advanced queue and orchestration system because every source,
fact, graph edge, label, and model-derived finding can create follow-up work. The
system should be deterministic enough to run locally, but structured enough to
map to Redis/KEDA, Temporal, Argo, or Celery in cloud deployments.

The core contract is:

```text
finding -> state transition -> priority policy -> research task -> worker lane -> evidence -> next transition
```

## Shared State Model

Published catalog components keep the public `lifecycle` field:

- `experimental`
- `beta`
- `stable`
- `deprecated`

Operational objects use richer states from `schemas/_common.schema.json`:

- `source-record`
- `fact-record`
- `normalized-object-record`
- `entity-record`
- `label-record`
- `dimension-record`
- `review-ticket`
- `object-factory-job`
- `research-task`
- `capability-request`

Every operational object can carry:

- `state`
- `state_history`
- `priority`
- `priority_signals`
- `queue_policy`

Facts additionally carry `fact_state`, or `state` in `fact-record`, so Baltor
can distinguish:

- candidate found in upload;
- one source found;
- two independent sources found;
- authoritative source found;
- needs second source;
- needs reconciliation;
- needs trust review;
- ready for adoption;
- served current;
- superseded or rejected.

This gives the system memory. A useful one-source fact found yesterday is not a
dead end; it is a scheduled follow-up.

## Queue Lanes

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

Each lane can run on the same local SQLite queue during development. In cloud,
each lane maps to a queue key and KEDA-scaled worker pool.

## Priority Signals

Priority should be explainable. A queued task stores raw signals plus the
resolved policy decision.

Core signals:

- `risk`: legal, compliance, safety, financial, or customer harm risk.
- `customer_impact`: how many customers, workflows, or served packs depend on it.
- `agent_usage`: how often agents request this fact or context region.
- `source_authority`: strength of currently found source.
- `source_count`: independent source count.
- `freshness_age_hours`: time since last verification.
- `failed_attempts`: number of failed searches or worker attempts.
- `deadline_hours`: hours until the fact becomes operationally urgent.
- `injection_risk`: source spam, prompt-injection, or hijack risk.
- `manual_review_cost`: expected burden of asking a human.

The priority policy resolves:

- `lane`
- `priority`
- `priority_score`
- `reason_codes`
- `not_before`
- `deadline_at`
- `max_attempts`
- `backoff`
- `dedupe_key`
- `cost_estimate`
- `budget_policy`

The important product behavior is that users should rarely double-check facts.
Manual review is a terminal fallback after cheaper deterministic, search, and
Hermes/OpenClaw workers have either failed or found genuine ambiguity.

## Default Policy

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

## Budget And Cost Policy

Every queued task should carry a planning estimate, even when the estimate is
small. This keeps local development, KEDA workers, Temporal activities, Argo
batch jobs, and future hosted billing aligned around one task envelope.

The shared fields are:

- `cost_estimate`: estimated total, floor, ceiling, search calls, browser
  seconds, worker seconds, GPU seconds, and line items;
- `budget_policy`: tenant budget remaining, task ceiling, monthly ceiling,
  budget-used percent, action, and reason codes.

Budget actions:

| Action | Meaning |
|---|---|
| `allow` | enqueue immediately |
| `batch` | enqueue, but prefer async/batch processing when latency allows |
| `require_approval` | route to `approval_required` until tenant/admin approval or an explicit budget override exists |
| `block` | route to `budget_blocked` because the remaining tenant budget is insufficient |

The default helper in `scripts/context_workers/priority.py` estimates each
research task from its `task_type`, priority, failed attempts, and usage signals.
The estimate is not a customer invoice. It is an orchestration guardrail that
prevents a rare hard case from silently turning into an unbounded model, browser,
or GPU bill.

Production routers should enforce:

- lane-level concurrency caps for `research`, `review`, `browser`, and `gpu`;
- tenant monthly ceilings;
- per-task ceilings for Hermes/OpenClaw/frontier lanes;
- batch routing for nonurgent expensive work;
- ledgered overrides for any approval-required task.

Malformed, unsupported, or repeatedly failing tasks should move to
`failed_permanently` after the retry budget. Do not mix these with
`approval_required` or `budget_blocked`; each state answers a different operator
question.

The local runner already models the operator flow:

- `--queue-list approval_required` shows tasks waiting for approval.
- `--approve-job <job_id>` requeues an approved task with override metadata.
- `--requeue-budget-blocked-job <job_id>` requeues after a budget policy change.
- `--requeue-failed-job <job_id>` requeues after the producer or worker has been
  fixed.

## Orchestration Shape

Local:

```text
SQLite queue -> scripts.context_workers.runner -> JSONL ledger
```

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

Managed queue, database, object-storage, email, secrets, and scheduler services
should be preferred when they reduce operational drag. K8s should be reserved
for execution pools that need dependency control, browser sandboxing,
adversarial audit isolation, GPU placement, or batch orchestration. See
`baltor-worker-operating-model.md`.

Temporal should own long-running customer-visible workflows:

- connector sync;
- source diff;
- multi-day second-source search;
- approval-free adoption when policies pass;
- rare review gate;
- serving package generation.

Argo should own bounded batch DAGs:

- rebuild a tenant graph;
- re-OCR a corpus;
- re-embed all claims;
- run an N-pass reindex.

Celery can be an adapter for Python task ergonomics, but it should not define the
product contract. The product contract is the task envelope, state history, and
priority policy.

## State-Driven Requeueing

Every run should scan active records for requeue triggers:

- `one_source_found` older than 24 hours -> second-source search;
- `needs_second_source` with high agent usage -> urgent second-source search;
- `needs_reconciliation` -> verify lane;
- `needs_trust_review` -> adversarial review;
- `needs_archive_capture` -> archive lane;
- `served_current` with stale freshness SLA -> refresh lane;
- `failed` with retryable reason -> backoff retry;
- `failed` after max attempts -> Hermes/OpenClaw or rare review;
- `superseded` -> graph/index propagation.

The requeue process must dedupe by `(tenant_id, task_type, fact_id, source_id,
target_url)` so repeated agent requests raise priority without flooding the queue.
The current deterministic helper emits this as `queue_policy.dedupe_key` for
worker-created follow-up tasks.

## Research Task Examples

Examples of standardized task types:

- `web.price.check`
- `web.statute.read`
- `web.site.search`
- `web.business.address.find`
- `web.business.hierarchy.find`
- `web.news.mna.scan`
- `docs.capability.lookup`
- `verify.second_source.find`
- `verify.official_source.find`
- `source.trust.score`
- `source.archive.submit`

These tasks all use the same envelope and differ only by payload and worker
capability. This is how Baltor can add new research skills without creating a
new orchestration system each time.

## Implementation Hooks

Current hooks:

- shared schema defs in `schemas/_common.schema.json`;
- operational schemas for facts, research tasks, source records, jobs, entities,
  labels, dimensions, reviews, and normalized objects;
- deterministic policy in `scripts/context_workers/priority.py`;
- worker follow-up task emission in `scripts/context_workers/tasks.py`.
- lifecycle requeue scanning in `scripts/context_workers/requeue.py`;
- task cost and budget helpers in `scripts/context_workers/priority.py`;
- adversarial routing and requeue fixtures in
  `scripts/context_workers/adversarial_fixtures.py`.

Run:

```bash
python -m scripts.context_workers.runner --adversarial-fixtures
python -m scripts.context_workers.runner --requeue-scan facts-and-sources.json
```

Next implementation steps:

- persist fact records and research tasks in Postgres;
- add lane-specific queue keys as shared constants;
- promote the lifecycle scanner into a scheduled local/Temporal/KEDA job once
  fact records are persisted;
- add worker dashboards for queue depth, oldest task, ETA, retry count, and
  blocked tasks;
- add Temporal workflows for source sync and fact adoption;
- add Argo templates for corpus-scale batch runs.
