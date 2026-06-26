# Infra scale-decision ports — Temporal · Postgres/ClickHouse · Vespa · Redpanda

> Decision rationale, 2026-06-25. Port implementation: `src/teleon/infra/scale_ports.py`. serves_truth=false.

## What this is

The scale review (`docs/architecture/scale-architecture-review-2026-06-25.md`) found the principles
scale-correct but the substrate single-node: JSONL files re-read whole each cycle (O(n)/cycle), lexical
O(n) cosine search, single-process daemons, git-as-firehose. The fix is a **substrate swap, not a
redesign** — and the swap must not couple callers to any one product.

So each heavy backend sits behind an **agnostic port** (the same pattern as `src/teleon/llm_port.py` and
the tier-backend swap in `src/teleon/storage/record_store.py`): callers depend on a role, not a vendor.
Choosing/replacing the real backend is a **deploy-time config change** (a client lib + an endpoint env
var), never a caller change.

| Role (caller selects by) | Real backend | Serves which existing tier | Why this backend |
|---|---|---|---|
| `orchestrator` | **Temporal** | operational (compute) | Durable workflow orchestration — the scale form of the autonomy loops: durable queue + stateless idempotent workers, retries/backpressure/DLQ. Addresses review #4 (single-process daemons, no queue). |
| `oltp` | **PostgreSQL** (+pgvector) | **operational** | Indexed hot rows + relationships at request time — the active product rows. Already the operational tier's `cloud_backend` in `architecture/storage_tier_policy.json`; `PostgresRecordStore` is the matching record-store swap. |
| `olap` | **ClickHouse** | **history** | Columnar aggregates over the append-only event log — analytics/rollups at billions+ without touching the OLTP path. Already named as the history tier's warehouse backend in the tier policy. |
| `vector` | **Vespa** | **operational** | ANN semantic search at scale (learned embeddings, HNSW), indexed **incrementally from the CDC stream** — not whole-file rebuilds. Addresses review #3 (lexical O(n) cosine is dead past ~100k). |
| `stream` | **Redpanda** | **history** | The CDC / event-log **spine**: immutable, content-hashed, **replayable** events; Kafka-API so consumers are standard. This is the data-plane source of record from which OLTP/OLAP/vector mirrors are rebuilt (review target architecture + #2 "git is a projection, not the firehose"). |

This is the **OLTP/OLAP split** the review calls for: Postgres serves transactional reads/writes;
ClickHouse serves analytical aggregates; neither contends with the other. Both are downstream
**materializations of the Redpanda log** — the log is the source of truth, the stores are rebuildable
indexes (exactly the `record_store` "JSONL mirror is the on-disk source, the db is a rebuildable index"
contract, lifted to the event log).

## Mapping to the existing storage tiers

`architecture/storage_tier_policy.json` already defines three tiers; these ports are how the **cloud
backend** column gets realized, with no new framing:

- **config** — stays whole-file git-tracked JSON (git *is* the store). No infra port; these ports never
  touch config-tier data.
- **operational** (`local: sqlite_wal → cloud: postgres`) — `oltp` (Postgres) + `vector` (Vespa for ANN;
  pgvector remains the in-Postgres option). The hot, queried-at-runtime rows.
- **history** (`local: sqlite_wal → cloud: warehouse`) — `stream` (Redpanda = the CDC/event-log spine
  that *feeds* history) + `olap` (ClickHouse = the partitioned columnar warehouse the policy already
  names). The append-only, billions-to-trillions tier.

`orchestrator` is the **compute** plane (how the loops run), orthogonal to where data lives — it drives
writes *through* the same record-store/stream ports, so it introduces no new storage authority.

## Honest-unavailable + the local-fallback story

Every role has **two** adapters behind the port:

1. A **real adapter** that is **honest-unavailable**: `available()` is `True` only when its client lib is
   importable **and** an endpoint env var is set (a deterministic, no-I/O probe — like
   `ProviderLLM.available()` checking `bool(key)`). When the lib or endpoint is absent, `available()` is
   `False` and **every op raises `InfraUnavailable` — it never fabricates a result**. (Same honesty as
   `record_store`'s unwired cloud backends, which name their swap contract rather than silently degrade.)
2. A **local in-memory fallback** (always available, deterministic) so **the descent still runs offline**:
   an in-process workflow runner, a dict-backed KV table, a list-backed columnar aggregator, a
   brute-force cosine ANN, and an append-only log with per-consumer-group offsets (real Kafka/Redpanda
   semantics, in memory).

`select_infra(role)` returns the real adapter **iff it is configured**, else the local fallback — and the
choice is honest: read `port.is_fallback`. `infra_status()` reports, per role, the backend, the tier it
serves, whether the real backend is configured, which port was selected, and **why** (e.g. "no endpoint
configured (set one of TEMPORAL_ADDRESS, TEMPORAL_HOST)").

This means: **today, with nothing installed, the whole loop runs on the local fallbacks** (proving the
motion end-to-end). **In production, setting the lib + endpoint env flips each role to its real backend
with zero caller change** — the substrate swap the scale review prescribes, made one config flip at a
time. serves_truth=false throughout (infrastructure moves/queries/indexes records; it is never itself a
source of truth).

## Endpoint env vars (the only config to flip)

| Role | Client lib(s) | Endpoint env (first set wins) |
|---|---|---|
| `orchestrator` | `temporalio` | `TEMPORAL_ADDRESS`, `TEMPORAL_HOST` (+ optional `TEMPORAL_TASK_QUEUE`) |
| `oltp` | `psycopg` / `psycopg2` | `POSTGRES_DSN`, `DATABASE_URL` |
| `olap` | `clickhouse_connect` | `CLICKHOUSE_URL`, `CLICKHOUSE_DSN` |
| `vector` | `vespa` (pyvespa) | `VESPA_ENDPOINT`, `VESPA_URL` (+ optional `VESPA_SCHEMA`) |
| `stream` | `confluent_kafka` / `kafka` | `REDPANDA_BROKERS`, `KAFKA_BOOTSTRAP_SERVERS` |

The role → (backend, libs, envs, tier) table is single-sourced in `_ROLES` in
`src/teleon/infra/scale_ports.py`; this doc must not re-type those values out of sync.

## Verify

```bash
PYTHONPATH=. python3 src/teleon/infra/scale_ports.py --self-test   # offline: all real backends honest-unavailable; fallbacks run
PYTHONPATH=. python3 src/teleon/infra/scale_ports.py --status      # honest per-role view of what's configured here
```
