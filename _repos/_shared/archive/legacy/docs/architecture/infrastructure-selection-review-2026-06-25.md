# Infrastructure selection review — are these the best choices?

> 2026-06-25. Honest, alternatives-considered review of the infra picks (DB, vector, object/blob/file, git, streaming,
> orchestration, IaC) against the planned scale (billions→trillions). **The load-bearing decision is the AGNOSTIC
> PORTS** (`record_store`, execution-provider, LLM, queue) — they let us run simple locally and swap to scale-native
> backends *without a rewrite*. So "best choice" is per-tier, chosen behind the port. serves_truth=false.

## Per-category verdict
| Category | Currently | Verdict | Best at scale | Action |
|---|---|---|---|---|
| **Transactional / curated metadata** | Postgres | ✅ keep | **Postgres** (mature, relational, JSON, pgvector, transactions) | keep — it's the right OLTP default |
| **High-volume firehose + telemetry + action-ledger** | (lumped into Postgres/JSONL) | ⚠️ **wrong tool** | **ClickHouse** (columnar, billions of append rows, cheap aggregations) — or BigQuery managed | **SPLIT the DB tier:** Postgres OLTP + ClickHouse OLAP firehose. Don't put billions of append-only rows in Postgres |
| **Vector / ANN search** | pgvector / Vectorize (planned) | ⚠️ ok to ~10-50M only | **Vespa** (unified lexical+vector+structured hybrid at scale — = our exact hybrid search) · **Turbopuffer/LanceDB** (object-backed, cheap at billions) | pgvector for hot/curated; **evaluate Vespa to collapse SQLite-index + pgvector + inverted-index into ONE scale engine** |
| **Object / blob storage** | R2 | ✅ **well-chosen** | **R2** (S3-compatible, **zero egress** — best cost for read-heavy) | keep; MinIO local; S3/GCS as agnostic peers |
| **File storage (POSIX)** | — | ✅ N/A | content-addressed **object** storage, not a filesystem | correct — we don't need EFS/NFS |
| **Git / code** | GitHub, branch=promotion | ✅ keep (curated/code only) | **GitHub** (ecosystem, Pages, Actions) | keep; firehose stays OUT of git (pointers) — already planned. GitLab/Gitea if self-host CI needed |
| **Streaming / CDC spine** | Cloudflare Queues (planned) | ⚠️ too light for the log | **Redpanda** (Kafka-compatible, lean) + Debezium CDC + Flink | Redpanda for the trillion-event log/replay; Cloudflare Queues only for edge/light |
| **Cloud ORCHESTRATOR (the loops)** | single-node Python daemons | ❌ **the real gap** | **Temporal** (durable, retryable, idempotent long-running workflows = exactly our discover→enrich→populate→index loops) + **Dagster/Prefect** or **Flink/Materialize** for the data pipeline | adopt Temporal as the loop runtime; daemons → Temporal workers |
| **Local orchestrator** | docker-compose + Tilt + emulators | ✅ keep (verified `local_go_live_ready=True`) | docker-compose/Tilt (kind/k3d if k8s-parity needed) | keep |
| **IaC** | OpenTofu (`deploy/tofu`) | ✅ keep | **OpenTofu** (open, vendor-neutral) | keep; Pulumi if you prefer code-based IaC |
| **Edge / compute** | Cloudflare Workers + containers (Fly/Cloud-Run) | ✅ but | Workers for edge; the LOOPS belong under Temporal, not raw containers | wire loops → Temporal workers (with #orchestrator) |

## What's well-chosen (keep)
R2 (egress-free object store) · Postgres as the OLTP/curated store · GitHub for the code/curated projection ·
OpenTofu IaC · docker-compose+Tilt for local · the **agnostic ports** (the most important decision — everything below
is swappable).

## What to change (ranked)
1. **Adopt a real orchestrator — Temporal — for the autonomous loops** (durable workflows, not single-node daemons).
   This is the biggest gap in "do we have clear orchestrators for cloud." Pairs with Dagster/Flink for the pipeline.
2. **Split the database tier**: Postgres (OLTP/curated) **+** ClickHouse (firehose/telemetry/action-ledger). Putting
   billions of append rows in Postgres is the wrong tool.
3. **Pick a scale vector store**: pgvector for hot; **seriously evaluate Vespa** (one engine for our lexical+vector+
   structured hybrid search at billions) or Turbopuffer/LanceDB (cheap, object-backed). Don't ride pgvector to billions.
4. **Redpanda/Kafka for the CDC/event-log spine** (replay, Debezium, stream processing), not Cloudflare Queues alone.

## Do we have clear local + cloud orchestration? (honest)
- **Local: yes** — docker-compose (`deploy/docker-compose.localtest.yml`) + Tilt + `local_emulators/` + tunnels;
  the three local-readiness checks PASS (`local_go_live_ready=True`).
- **Cloud: partially** — we have IaC (OpenTofu) + containers (Fly) + Cloudflare edge, but **no chosen workflow
  orchestrator (Temporal) or stream processor (Dagster/Flink)** for the loops, and the DB/vector scale picks above are
  unresolved. That's the work to make `cloud go_live_ready=True` honestly.

## The unifying principle
Keep **everything behind the agnostic ports**. Then the stack is: **dev** = SQLite + local FS + compose; **scale** =
Postgres(OLTP) + ClickHouse(OLAP) + Vespa/Turbopuffer(vectors) + R2(object) + Redpanda(CDC) + Temporal(orchestration)
+ Cloudflare(edge/Pages/Workers-AI) + GitHub(code) — chosen per tier, swapped by config, never a rewrite.
