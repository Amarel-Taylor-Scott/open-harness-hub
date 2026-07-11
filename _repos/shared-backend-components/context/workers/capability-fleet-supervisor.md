# Capability-Aware Worker Fleet Supervisor

**Purpose.** Dynamically start, reuse, batch, drain, and stop capability workers based on a DB-backed task
ledger, worker heartbeats, SLA, batch thresholds, and queue age — so on-demand work meets SLA and batch work
is cost-efficient. Rides the EXISTING durable-worker substrate (queue/lease/idempotency/retry/DLQ/outbox,
two-process exactly-once); it is NOT a second worker framework or queue.

**Owner.** `_repos/baltor/backend/src/baltor/workers/{fleet_ledger,fleet_supervisor,local_spawn_manager}.py` +
`scripts/capability_worker.py`. Registries: `architecture/worker_{capability_registry,lifecycle_policies,
batch_policies,sla_policies}.json`. Contracts: `schemas/workers/*.v1`.

## Architecture decision: DB ledger = truth; Pub/Sub/KEDA = optional wake-up/scale
The **`FleetLedger` (DB-backed) is the source of truth** for task status, atomic claims, leases, attempts,
heartbeats, SLA/batch thresholds, idempotency, failures, and provider fallback. Pub/Sub / SSE / KEDA are
**optional** latency/scale accelerators — a lost wake-up never loses a task because the worker always reads
the ledger. Local now: in-memory + SQLite (`BEGIN IMMEDIATE`). Later: Postgres `SELECT … FOR UPDATE SKIP
LOCKED` + KEDA `ScaledObject`/`ScaledJob` over queue metrics — WITHOUT changing the task/worker contracts.

## The invariant (carry in every worker prompt)
**Workers are stateless capability executors and do NOT own a task until an atomic claim succeeds.** Starting
a worker may pass `capability_id`, a queue selector, and an optional `bootstrap_task_id` — but never grants
ownership. The supervisor is the capacity planner; the worker is the executor; the ledger is the truth.

## Lifecycle
starting → warm → (claim) busy → ack/nack → cooldown (DRAIN compatible work) → stop on idle. A worker that
completes a task polls immediate/next-available/batch-ready work during cooldown before shutting down.

## Supervisor decisions (one tick per capability)
- **A** on-demand + no worker → **spawn**.
- **B** on-demand + warm worker with free capacity meeting SLA → **use_existing**.
- **C** on-demand + workers can't meet SLA (no free slot / too slow) → **spawn** another.
- **D** batch below `batch_min` and within `max_wait` → **batch_wait**.
- **E** batch at `batch_min` → **batch_dispatch**.
- **G** batch below threshold but `max_wait` elapsed → **batch_dispatch (partial)** (anti-starvation).
- **H** expired lease → **reclaim** (stale worker's tasks return to the queue).
- **F** retry on a failed task with a next provider → **fallback**.
- unknown capability → **reject** (never spawn for an uncataloged capability).

## Atomic claim + leasing + retry/DLQ + idempotency
`claim_task` returns ownership to exactly one worker (oldest ready task; second claimant gets `None`).
Leases expire → `reclaim_expired_leases` re-queues. `ack`/`start`/`progress` require the owning worker.
`nack` increments `attempt`; on `attempt >= max_attempts` (or non-retryable) → **dead/DLQ**, else re-queued.
Same `idempotency_key` → same task (no duplicate side effects). A worker may not claim outside its
registered capabilities.

## Provider fallback
A failing task retries the primary provider, then falls back to the next in `fallback_order` (the ledger
advances the provider by attempt index), preserving the same input contract and single task row; final
failure goes dead.

## Policies
Lifecycle: cold_start_each_task · burst_keepalive · warm_pool · hot_pool · scheduled_batch. Batch:
on_demand_immediate · next_available · batch_min_5 · batch_min_25 · batch_min_100. SLA: interactive_10s/30s ·
standard_2m · batch_15m · offline_24h. Capabilities map to default policies + providers + fallback_order +
queues + estimated startup/task ms.

## Proofs
`scripts/check_worker_fleet_schema.py`, `check_worker_atomic_claim.py`, `check_worker_fleet_supervisor.py`,
`capability_worker.py`, `check_worker_status_progress_tracking.py`, `check_worker_provider_fallback.py`,
`check_local_spawn_manager.py`, `check_worker_fleet_redteam.py`, `check_worker_fleet_supervisor_full_stack.py`.

## K8s / KEDA mapping (later)
warm/hot pools → Deployment; queue-driven → KEDA `ScaledObject` over the ledger/queue metric; batch →
`ScaledJob`/Job work-queue pattern (Pods pull until empty); preStop → cooldown/drain. SQLite `BEGIN IMMEDIATE`
→ Postgres `FOR UPDATE SKIP LOCKED`. The DB ledger stays the source of truth; KEDA only decides replica count.

## Limitations / Next (OPP-worker-fleet-surface)
Lean core = ledger + atomic claim + capability registry + lifecycle/batch/SLA policies + supervisor decisions
+ worker lifecycle + spawn manager + provider fallback + proofs + docs. Deferred: SQLite/Postgres-backed
ledger persistence wired to the live dispatch path, `/api/fleet/*` + `/fleet` UI, a metrics dashboard, the
optional WorkerWakeupPort (pub/sub/KEDA), and K8s yaml templates.
