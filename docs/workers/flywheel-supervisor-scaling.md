# Lightweight Flywheel Supervisor Scaling (C-FLEET-3)

The control plane stays cheap (see `operating-model-always-on-vs-scale-to-zero.md`). When one supervisor
process can no longer inspect every queue / shard / fact fast enough, it scales as a **replicated control
plane** — NOT by doing worker work in-process.

> **Rule:** Flywheel = scheduler / supervisor / health loop. Workers = execution. The DB task ledger is
> the **source of truth**.
> The supervisor only enqueues/starts workers and records coordination + decisions. If it becomes
> CPU-heavy, it is doing worker work by mistake.

## Four scaling levels

1. **One local supervisor** — current shape: one process, one ledger, local subprocess spawn.
2. **Active/passive** — N supervisors, one holds the **leader lease** for singleton duties (global proof
   sweep, migrations, review-pack generation). If the leader dies, its lease expires and a standby takes
   over.
3. **Sharded** — split high-volume scans (queues, tenants, source TTLs, heartbeats) into **shards**; each
   supervisor claims one or more **shard leases** and only scans its shard. Avoids the anti-pattern
   "every supervisor scans every task every 10s."
4. **K8s/KEDA** — supervisor `Deployment` (`minReplicas: 1–2`, small CPU) owning shards by lease; worker
   pools scale separately via KEDA/HPA/Jobs.

## The five coordination records (`supervisor_ledger.py`)

`supervisor_instances` · `supervisor_leases` · `supervisor_shards` · `supervisor_ticks` ·
`supervisor_decisions`. Modeled in-memory now; maps to SQLite/Postgres later with the **same CAS
semantics**: a lease is acquirable iff unheld, expired, or already mine
(`UPDATE … WHERE lease_until < :now OR owner_id = :me`).

## Safety invariants (proven)

- **Singleton via leader lease** — two supervisors never both run a singleton duty.
- **Failover** — when the leader's lease expires, a standby acquires it; renewal keeps it.
- **Shards distribute** — different supervisors own different shards; stale shard leases are reclaimable.
- **Idempotent decisions** — the same due job → the same `idempotency_key` → the same decision; two racing
  supervisors never enqueue duplicate work (no duplicate spawn).
- **Execution stays in workers** — the supervisor records decisions/commands; workers claim atomically
  from the task ledger.

## When to scale the supervisor (`supervisor_metrics.py`)

Scale the CONTROL PLANE (add a shard owner / standby) on **coordination pressure**, not CPU:
- tick `duration_ms` > the interval budget over many ticks (`over_budget_ratio`),
- `shard_lag_s` rising (an owner is behind/stale),
- due backlog (`latest_due_task_count`) piling up.

Do **not** scale it because browser/GPU/PDF/research tasks are slow — those scale the relevant **worker
bucket**, not the flywheel.

## K8s/KEDA mapping

| Concern | K8s |
|---|---|
| Supervisor fleet | `Deployment` `minReplicas: 1–2`, small CPU; owns shards by lease |
| Leader/shard leases | rows in Postgres (`FOR UPDATE SKIP LOCKED` / conditional update) |
| Worker pools | scale separately (KEDA `ScaledObject`/`ScaledJob`, HPA) — see `k8s-keda-worker-mapping.md` |

## Deferred (`OPP-fleet-lifecycle-surface`)

Persisting the coordination tables (SQLite→Postgres) on the live path, a real multi-process failover
harness, and wiring the leader/shard managers into `baltor_flywheel.py`'s watch loop.

## LIVE SUPERVISOR CLAUSE (carry in every supervisor/flywheel pass)

Offline fleet proofs are NOT enough. If supervisor scaling is deferred, the next pass must wire leader
leases, shard leases, idempotent decisions, capacity snapshots, and spawn decisions into the REAL
`baltor_flywheel.py --watch` loop. Two `--watch` processes must run safely against one DB; exactly one
leader may execute singleton duties; shard ownership must be exclusive; a leader kill must fail over to a
standby; and duplicate scheduling must be prevented by idempotency keys. The finish line is the live watch
loop safely coordinating multiple supervisors against one durable ledger — proven by
`check_live_supervisor_two_process` — not "+N deterministic offline proofs".
