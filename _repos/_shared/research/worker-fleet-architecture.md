# Worker-fleet architecture — patterns, scaling, fault tolerance (owner research, 2026-06-05)

Captured from owner research on running many Python workers (K8s/serverless) that synchronize,
communicate, and stay fault-tolerant + queueable. **Status:** reference/design. External cloud-service
+ company-example claims are owner-provided (with citations) — **pending independent verification**;
the repo's **verified** backend catalog (`data/backend-tools.yaml` + `research/backend-tool-
verification.md`) remains the source of truth for tool selection (it already names DBOS/Temporal as
durable engines, KEDA as the autoscaler, Graphiti over archived Kuzu — honor the do-not-reintroduce
list).

## The core answer
For a large fleet of K8s Python workers, **do NOT do worker-to-worker coordination.** Standard shape:
```
producer/API → durable work distribution (queue | pub/sub topic | event log | DB queue | workflow task queue)
            → many STATELESS workers → durable state + idempotency table → result event / status row / next step
```
- **A queue/pub-sub layer is (almost) always needed.** Queue = one worker per task (commands); pub/sub
  = many consumers per fact (events); event log (Kafka) = high-throughput, replay, ordered-per-key.
- **An orchestration layer is needed ONLY when one "job" is a durable multi-step process** (retries
  across services, timers, compensation/rollback, fan-out/fan-in, human approval, resume-after-crash).
- **Kubernetes runs + scales workers; it does NOT give durable task ownership** (acks, DLQ, replay,
  exactly-once business effects). That ownership lives in the queue / broker / log / DB lease /
  workflow engine.

## The four planes (mental model)
`ingress/producer → durable work distribution → worker hosting → durable state → autoscaling signal`
Decide independently: **what owns the task**, **where it runs**, **what owns durable state**, **what
drives scaling** (backlog/lag/oldest-unacked-age — NOT just CPU; queue consumers are usually I/O-bound).

## Non-negotiable fault-tolerance invariant (every variation)
`durable claim → idempotent processing → durable result → ack/delete/settle/commit`
- assume **at-least-once** delivery → every job has a stable id; `processed_messages` table or natural
  idempotency (unique constraints); ack only AFTER durable success.
- **transactional outbox** to avoid dual-write (write business row + outbox row in one txn; relay
  publishes; consumers idempotent). DLQ + bounded retries + backoff/jitter; graceful SIGTERM drain.

## Patterns (least-ops → most-control)
1. **Serverless queue consumers** — SQS→Lambda / PubSub→CloudRun / ServiceBus→Functions. Short stateless jobs.
2. **Managed container pool** — SQS→ECS-Fargate / PubSub→Cloud Run worker pool / ServiceBus→Container Apps. Best default for longer Python workers.
3. **K8s event-driven fleet** — managed queue → **KEDA** ScaledObject/ScaledJob (scale on backlog/age) → HPA pods → Karpenter/Cluster-Autoscaler nodes.
4. **One container per job** — AWS/GCP/Azure Batch, Cloud Run Jobs, KEDA ScaledJob, Argo/K8s Jobs. Heavy/GPU/isolated work.
5. **Workflow-orchestrated** — Temporal/Cadence/Conductor or Step Functions/Workflows/Durable Functions. Durable multi-step state.
6. **Event stream/log** — Kafka/Kinesis/PubSub/EventHubs + consumer groups. Replay, audit, many consumers.
7. **DB-backed queue** — Postgres `SELECT … FOR UPDATE SKIP LOCKED`. Underrated at moderate scale; fewest moving parts.
8. **Sharded queues / priority lanes** — per-tenant/priority/GPU/retry/DLQ queues to stop one tenant starving others.
9. **Hybrid orchestrator + queue** — workflow owns state, queues own high-throughput dispatch (AI/doc pipelines).
10. **Control-plane / data-plane split** — "decide what happens" (scheduler/quotas/leases/routing) vs "do the work" (workers).

Scaling: `total_concurrency = replicas × procs × async_tasks × batch`. Horizontal first for stateless
workers (more pods/tasks/consumers/partitions); vertical where per-worker efficiency wins (memory-heavy,
model loads, CPU-bound, warm caches). HPA = pod count; VPA = pod size (use carefully together); KEDA =
event-source-driven; Karpenter/Autopilot = nodes.

## Where Baltor sits (mapping — connect, don't recreate)
Baltor today is a **single-process in-proc bus** (`context_events.EventBus`, pub/sub PUSH) + a
**timer-pull watcher** (`baltor_flywheel.py --watch`) + **HTTP push triggers** (admin POST endpoints).
That is the right *contract*; the fleet upgrade is a **backend swap behind ports**, not a rewrite:
- **Bus → broker SEAM:** `EventBus.publish/subscribe` is the seam. A durable broker (RabbitMQ quorum /
  SQS / NATS JetStream / Kafka) is a swap-in that keeps the same publish/subscribe contract. Engines
  already take `bus=None` (duck-typed) — a broker-backed bus is a drop-in.
- **Flywheel → KEDA/queue SEAM:** the `--watch` poller is the local stand-in for a KEDA-autoscaled
  worker Deployment consuming a queue (scale on backlog/oldest-unacked-age). `tick()` = the worker body.
- **Durable multi-step → workflow SEAM:** the verified catalog already picks **DBOS/Temporal** for the
  durable engine; today's `run_full_pipeline` / `integrate_cfpb` are the in-proc stand-ins.
- **Idempotency/outbox already half-there:** content hashes + receipts + `processed`-style dedup +
  CDC are the spine of idempotent consumers + outbox; formalize a `processed_messages` table on load.
- **Observability:** emit the bus events as **OTel GenAI spans** (see `context-object-model-and-
  coralogix.md`) → any backend (Coralogix) observes the fleet. KEDA scales on the same signals.

**Sequencing (no-pip-friendly first):** (1) document the broker/KEDA/workflow SEAMs as capability
ports (done-ish via the bus + flywheel); (2) add a `processed_messages`/idempotency contract + a
transactional-outbox schema as a labeled SEAM; (3) a local `SKIP LOCKED` Postgres-queue reference impl
(pattern 7) as the lowest-dep durable queue; (4) real broker/KEDA only when scale demands it (owner
decision — paid/cluster resources are parked). Verify any new tool against the catalog before adoption.

## Real examples (owner-cited; verify before quoting externally)
DoorDash (Celery/RabbitMQ 900+ tasks → Kafka under outages) · Uber Cadence (durable workflows, billions
of executions) · Gorgias (Postgres+RabbitMQ+Flask+Celery on K8s) · Atlan (Argo→Temporal migration) ·
AWS EKS+SQS+KEDA, GCP Cloud Run worker-pools autoscaling on Pub/Sub, Azure Container Apps Jobs — the
canonical reference patterns.
