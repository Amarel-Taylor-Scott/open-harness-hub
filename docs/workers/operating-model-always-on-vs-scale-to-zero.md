# Operating Model: 24/7 Control Plane vs Scale-to-Zero Workers

**Decision (owner-confirmed, 2026-06-06):** yes — some flywheel-style work runs 24/7, and that is the
preferred posture. But the split is load-bearing:

> **The lightweight control plane stays awake 24/7. Expensive execution workers do not.**
> "Flywheel" never means "keep Selenium/GPUs/LLMs/open-ended agents running all night." It means a
> small supervisor stays awake enough to inspect queues, worker health, proof health, and stale facts;
> schedule work; start/stop workers; reclaim leases; and record telemetry — then go back to sleep.

## Always-on (cheap control plane)

| Loop | Job | Why 24/7 |
|---|---|---|
| Fleet supervisor | inspect queue/heartbeats/SLA/batch/leases/provider health; spawn/stop workers | the capacity planner |
| Proof/watchdog flywheel | run proof health, detect red, restart on PROOF_MODULES change (exact pid, no pkill) | keeps the system honest |
| Watch-policy scheduler | fragile facts, source TTLs, `next_verify_at`, source-change triggers | freshness ≠ correctness |
| Lease reclaimer | reclaim expired leases, retry eligible, DLQ poison | nothing stuck forever |
| Observability projector | update dashboard/dev/ops projections from durable state | visibility |
| Cost/utilization monitor | startup/active/idle burn, tasks-per-start, provider failure rates | feeds the recommender |

These mostly **sleep, poll, decide**. They are CPU-cheap. If one becomes CPU-heavy it is doing worker
work by mistake.

## NOT always-on by default (expensive execution) — lifecycle-policy controlled

Browser (Selenium/Playwright), GPU/model inference, large parser/OCR, open-ended research agents,
codegen, heavy embedding/vectorization. Governed by the C-FLEET-2 lifecycle policies:
`cold_start_each_task` · `burst_keepalive` · `warm_pool` (active hours) · `hot_pool` (only if
utilization justifies) · `batch_min_5/25/100` · `scheduled_batch_window`.

## The practical rule (per capability, every supervisor tick)

- on-demand task, no warm worker → **spawn**
- warm worker can meet SLA → **let it claim**
- warm worker would miss SLA → **spawn another**
- batchable → **wait** until `batch_min` or `max_wait`
- just finished → **cooldown**, drain compatible work
- nothing arrives in cooldown → **shut down**

Best of both: fast when needed, low idle cost when quiet, good utilization in bursts, safe replay
because the **DB ledger is truth**. KEDA maps this later (`minReplicaCount: 0`, `cooldownPeriod` for
scale-to-zero, HPA for 1→N); see `k8s-keda-worker-mapping.md`.

## DB ledger vs Pub/Sub

DB ledger = truth (state, claims, leases, attempts, failures, idempotency, SLA, receipts, heartbeats).
Pub/Sub (later) = wake-up accelerator only. A lost notification never loses work; a duplicate never
duplicates it (atomic claim admits exactly one).

## How the control plane itself scales

It scales as a **replicated control plane**, not by doing worker work: 1 active leader (singleton
duties) + N shard owners (high-volume scans), coordinated by DB leases + idempotent decisions. Built
in **C-FLEET-3** (`flywheel-supervisor-scaling.md`).
