# Scaling ingestion → facts: thousands of tenants × millions of documents

How the **local SQLite demo** maps, unchanged in shape, to a fault-tolerant fleet. The rule: the
**contract** (partition key, idempotency key, claim/ack/lease, DLQ, atomic-fact output) stays fixed;
only the **backend** swaps. Proven locally by `scripts/ingest/tenant_ingest.py --self-test` and the live
`/api/dev/tenant-ingest` route. Builds on `docs/architecture/{durable-runtime-plan,worker-fleet-architecture}.md`.

## The invariant that makes it scale
```
enqueue(tenant_id, doc) → per-TENANT queue lane (ingest.<tenant_id>)
   → STATELESS worker claims (lease) → decompose → ATOMIC FACTS → ack
   exactly-once via idempotency key  <tenant_id>:<doc_id>:<content_hash>
```
- **Partition by tenant** (`ingest.<tenant_id>`): one slow/huge tenant never starves another; lanes
  scale + fail independently. (Proven: acme + globex isolated.)
- **Idempotency = document VERSION** (`tenant:doc:content_hash`): re-ingesting the same version is a
  no-op; a changed version is a new job → **exactly-once business effects** under at-least-once delivery.
  (Proven live: re-ingest → 0 new / 1 duplicate.)
- **Stateless workers + lease**: any worker can take any job; a crash (no ack) → lease expires → another
  worker reclaims. (Proven: 3 concurrent workers process each doc EXACTLY once.)
- **Fact-level output**: each doc → atomic single-sentence facts (`ctx://…#field`) + held-out narrative
  sentences — the smallest citable/expandable unit.

## Local demo ⇄ scalable backend (swap behind the contract — NO rewrite)
| Concern | Local demo (now, no pip/cloud) | Scalable swap (later) |
|---|---|---|
| Work queue | `DurableStore` SQLite (`enqueue`/`claim`/`ack`/`nack`/DLQ) | SQS · RabbitMQ quorum · NATS JetStream · Pub/Sub — same enqueue/claim API |
| Worker | threaded/looped `drain()` in-proc | KEDA-scaled K8s Deployment (scale on oldest-message-age / lane depth) |
| Per-tenant lane | `ingest.<tenant_id>` queue name | one topic/queue per tenant or a tenant-keyed partition (Kafka key = tenant) |
| Idempotency | `processed`/`jobs.idempotency_key` UNIQUE | same key in Postgres `engine_runs` UNIQUE |
| Event log / evidence | SQLite `events` (hydrate on restart) | Postgres + object store; OTel spans → Coralogix |
| State store | SQLite | Postgres (objects/versions/facts/lineage) + S3 (raw) + pgvector (embeddings) |
| Orchestration | `tenant_ingest` enqueue/drain | DBOS/Temporal for the pass/document lifecycle |

The local code IS the seam: `tenant_ingest` calls only `DurableStore.{enqueue,claim,ack,nack,stats}` —
point those at a broker adapter and the fleet runs unchanged.

## Sizing (the math, not a claim)
`throughput = workers × concurrency_per_worker × batch ÷ avg_decompose_seconds`;
`drain_time = backlog ÷ (rate − arrival)`. For millions of docs: shard lanes by tenant (+ sub-shard a
whale tenant by doc-id hash), autoscale each lane on **oldest-message-age** (not raw depth — 12 stuck P0
docs > 1M tiny ones), cap per-worker concurrency to respect downstream (DB/parser/LLM) limits, and
dead-letter poison docs so one bad PDF never blocks a lane.

## Priority + isolation lanes (already the naming convention)
`ingest.<tenant>` for normal flow; `flywheel.p0.*` for proof/signoff gates; `flywheel.dlq` for poison.
Per-tenant quotas + a control-plane scheduler decide admission (Kueue-style) so no tenant monopolizes
the fleet.

## What's proven vs deferred
- **Proven now (local):** per-tenant lanes, idempotent-per-version, tenant isolation, fact-level
  decomposition, durable restart-survival, retry→DLQ, live `/api/dev/tenant-ingest`, AND a **standalone
  worker process** (`scripts/flywheel_worker.py`) — `scripts/check_durable_worker_parallel.py` runs **two
  worker PROCESSES** against one queue and proves exactly-once across processes (24 docs, split ~13/11,
  no double-process, no DLQ, measured drain). This is the C29 "scale one engine" acceptance test: more
  workers = more throughput, same contract.
- **Deferred (backlog, owner/infra decision — paid/cluster):** the actual broker/KEDA/Postgres swap
  (the worker becomes a KEDA-scaled Deployment of `flywheel_worker`); unstructured PDF docs via a Docling
  `ParserProvider`. Neither requires changing the contract above.
