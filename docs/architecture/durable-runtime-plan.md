# Baltor durable runtime — 3-plane architecture + pass plan (2026-06-05)

Owner architecture input, reconciled with what's now SHIPPED. The sentence we're building toward:
> Baltor's Dev Flywheel is an **event-sourced, proof-driven control plane** where ticks schedule work,
> engines execute through **durable per-engine queues**, proofs emit **evidence receipts**, and passes
> promote only after **replayable** automated checks and required **human signoffs**.

## Three planes (separate concerns)
1. **Control plane** — flywheel ticks, pass planning, backlog priority, orchestration decisions.
2. **Work plane** — per-engine queues, workers, retries, DLQs, leases, scaling.
3. **Evidence plane** — immutable event log, proof results, review packs, receipts, dashboard projections.

The dashboards stay the **builder's view** — they READ projections from the evidence plane; they are
NOT the orchestrator, queue, or source of truth. **One bus for evidence (audit/replay); many queues
for execution** (engines scale + fail differently).

## What's SHIPPED (the durable foundation — C27 core landed)
`scripts/durable_store.py` (stdlib `sqlite3`, ACID, WAL, **thread-safe** under ThreadingHTTPServer; no
broker/cloud/pip):
- **Durable event log** — every bus event persisted; **bus hydrates on restart** ⇒ the live stream
  SURVIVES a crash (proven: 51→51 across kill+restart; opt-in via `BALTOR_DURABLE_DB`).
- **Durable job queue** — `enqueue → claim(lease) → ack | nack(retry) → DLQ`; **crashed-worker
  recovery** via lease expiry; FIFO; **idempotency** table; **transactional outbox**. 16-check self-test
  in the flywheel (`durable_store`). This is the C27 inbox/outbox/idempotency/engine-run ledger, local.

This already gives flexibility: **per-engine queues + priority lanes are just queue NAMES** on the same
store (`enqueue("flywheel.commands.context_diff", …)`, `enqueue("flywheel.p0.proof_gate", …)`). The
SQLite backend is a **swap-behind-the-contract** (RabbitMQ/SQS/NATS/Kafka later) — same enqueue/claim API.

## Pass plan (reconciled with owner's C26–C31)
- **C26 — event envelope contract (NEXT).** Lock one envelope for every bus event + queue command:
  `event_id, event_type, schema_version, created_at, pass_id, tick_id, engine, engine_version,
  subject_type, subject_id, causation_id, correlation_id, trace_id, idempotency_key, priority, attempt,
  payload, evidence{receipt_uri,input_hash,output_hash}`. Build as a validator (`schemas/runtime/*` +
  a `--self-test`); keep `context_events` emitting the envelope. Gives durable causality: owner-ask →
  backlog → tick → command → engine-run → proof → pass → review-pack → projection.
- **C27 — durable work ledger. ✅ CORE DONE** (`durable_store`). Remaining: an `engine_runs` view +
  the contract proofs as named checks (`check_crash_before_ack_replays`, `…after_result_no_dup`,
  `…dlq_after_retry_budget`, `…duplicate_skipped`) — mostly covered by the durable_store self-test; promote
  to a dedicated `check_durable_runtime.py` when workers land.
- **C28 — one bus, many queues.** Route commands to per-engine queues (names below); workers no longer
  depend on dashboard/SSE; dashboard reads projection. Proofs: queue-routing, priority-lane routing, DLQ
  capture, projection lag.
- **C29 — scale one engine.** Run N stateless workers for `context_diff` (or `proof_runner`) off its
  queue, same idempotency key ⇒ no duplicate side effects; measure drain time. (Local: N threads/procs;
  cloud: KEDA on queue depth + oldest-message-age — see `research/worker-fleet-architecture.md`.)
- **C30 — pass lifecycle orchestration.** A lightweight orchestrator (or Temporal later) for
  owner-ask → tick → fan-out engine commands → fan-in proof results → review pack → promotion. Proofs:
  replay, partial-failure resume, review-pack-after-required-proofs.
- **C31 — human-signoff gate.** Model "AI drafts, humans sign off" as a RUNTIME lane (not just copy):
  `compliance_copy.proposed → human_signoff.requested → approve/edit/reject → completed`; a pass
  cannot promote compliance-sensitive output until the signoff proof passes. (Owner-decision content
  stays parked; the *gate mechanism* is principle-backed.)

## Per-engine execution model (from the proof list)
| family | model | scale |
|---|---|---|
| context_swarm/compress/diff/memory_block | stateless workers | 0→N horizontal |
| parser_router/parser_provider/document_decompose | CPU/mem-tuned workers | 0→N |
| ecfr/federal_register/sanctions feeds | **singleton w/ lease** (leader) | 1 active |
| make_review_pack/render_receipt/demo_run_export | job-per-pass | 0→few |
| validate_*/ci_check/check_* | proof-runner pool | parallel |
| check_live_pipeline/check_event_integration/baltor_acceptance | integration/release-gate | low concurrency |

**Priority lanes (queue names):** `flywheel.p0.{owner_ask,proof_gate,human_signoff}` ·
`flywheel.p1.{engine_build,eval_harness}` · `flywheel.p2.research` · `flywheel.bulk.review_pack` ·
`flywheel.retry` · `flywheel.dlq`. P2 must never block P0 proof gates.

**Autoscaling signals (not raw depth):** oldest_message_age, pending_by_engine, proof_age,
pass_to_green_duration, retry_count_by_engine, dlq_count_by_engine, provider_rate_limit_events,
projection_lag. (12 stuck P0 proofs > 1000 tiny jobs.)

**Cloud variants** (all behind the same contract; owner-decision/paid → parked): AWS SQS+ECS/Fargate +
Step Functions · GCP Pub/Sub + Cloud Run worker-pools + Workflows · Azure Service Bus + Container Apps +
Durable Functions. Verified catalog (DBOS/Temporal/KEDA) stays the tool source of truth.

## Flexibility/robustness improvements already in place
- Durability is **opt-in + non-breaking** (`BALTOR_DURABLE_DB` unset ⇒ in-memory, all proofs unchanged).
- Token-gate + poll-primary dashboards make the public surface robust through tunnels/proxies.
- `EventBus.restore()` is the clean rehydration seam; the bus stays the single evidence stream.
- The durable queue's `now` is injected ⇒ deterministic, testable, replayable.
