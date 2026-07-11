# K8s / KEDA Worker Mapping (C-FLEET-2)

How Baltor's local worker fleet maps to Kubernetes + KEDA **later**, without changing the task contracts
or worker categories. Today everything runs as local processes against an in-memory/SQLite ledger; these
templates (`infra/k8s/*.yaml.template`) are scaffolds for the production posture.

> **Invariant carried into K8s:** the **DB task ledger is the source of truth**. KEDA/Pub/Sub are
> optional wake-up / autoscaling signals. A worker always **claims atomically from the ledger** after
> wake-up. A lost wake-up never loses a task (the worker re-reads the ledger); a duplicate wake-up never
> duplicates work (the atomic claim admits exactly one).

## Lifecycle policy → K8s mapping

| Lifecycle policy | K8s mapping | Template | Ramp-up | Ramp-down |
|---|---|---|---|---|
| `cold_start_each_task` | `Job` | `capability-worker-job.yaml.template` | one Job per task | exits after the task |
| `burst_keepalive`, `cooldown_drain` | KEDA `ScaledObject` (scale-to-zero) | `capability-worker-scaledobject.yaml.template` | KEDA 0→1 on queue depth | KEDA `cooldownPeriod` → 0 |
| `warm_pool`, `hot_pool`, `high_priority_on_demand` | `Deployment` + HPA | `capability-worker-deployment.yaml.template` | HPA 1→N on load | min replicas stay warm |
| `batch_min_5`/`_25`/`_100` | KEDA `ScaledJob` | `capability-worker-scaledjob.yaml.template` | one Job per `batch_min` queued | Job exits when batch drained |
| `scheduled_batch_window` | `CronJob` | (use `ScaledJob` on a schedule) | fires on schedule | exits when window drained |

The `k8s_mapping` field on each policy in `architecture/worker_lifecycle_policies.json` is the single
source for this mapping.

## How the knobs line up

- **`minReplicaCount: 0`** (ScaledObject/ScaledJob) ⇒ scale-to-zero when idle — `burst_keepalive`/batch.
- **`cooldownPeriod`** ⇒ KEDA's ramp-DOWN-to-zero delay = the policy's `keepalive_after_task_seconds`.
- **HPA** handles **1→N**; **KEDA** handles **0→1** (per KEDA docs, `cooldownPeriod` applies to the
  scale-to-zero transition, while scaling up from one replica is the HPA's job).
- **`pollingInterval`** ⇒ how often KEDA reads the queue-depth trigger.
- **`terminationGracePeriodSeconds` + `preStop`** ⇒ graceful **drain**: stop claiming, finish the current
  task, then exit (never kill an in-flight task — maps to `drain_new_work_before_shutdown`).
- **`backoffLimit`** ⇒ maps to the ledger's `max_attempts` / DLQ.

## Postgres ledger (later)

Local SQLite `BEGIN IMMEDIATE` + `lease_until` → Postgres `SELECT … FOR UPDATE SKIP LOCKED` + `lease_until`
(skip-locked lets many workers claim from the queue table without contention). Same `CapabilityTask` /
`CapabilityWorker` contracts; only the storage backend swaps.

## What does NOT change

Worker categories (`worker_bucket_registry.json`), the lifecycle/batch/SLA policies, the atomic-claim
contract, the failure taxonomy, and the telemetry tables are identical local vs K8s. Only the spawn
mechanism (local subprocess → Job/Deployment) and the storage (SQLite → Postgres) differ.

## Deferred

Real cluster manifests, a KEDA install, a Postgres-backed ledger on the live dispatch path, and a
`WorkerWakeupPort` (Pub/Sub/KEDA) behind the seam — all tracked under `OPP-worker-fleet-surface`.
