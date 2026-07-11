# Cloud architecture — storage-first, serverless, scale-to-zero (all flexibility, none of the "everything hot" cost)

> Answers: can we run this in the cloud with ALL the flexibility/runtime/expandability but WITHOUT keeping everything
> hot and expensive? And: custom DBs + autoscaling, or managed autoscaling + custom? **Yes — via a storage-first,
> serverless, scale-to-zero stack where cost scales with USAGE (queries), not corpus SIZE, and idle ≈ $0.** The
> answer is a COMBINATION: managed serverless primitives for the commodity layers (storage/query/compute/scaling)
> + a thin CUSTOM layer for our moat (semantic ABI, graph solver, multi-model router, usage-driven tiering).
> Researched 2026-07-10 (see Sources).

## 0. The one principle

The cost trap is not *storing* everything — object storage is $0.02/GB. The trap is *keeping everything HOT* (in RAM).
So: **store EVERYTHING cold in object storage (all models, all facets, all representations — build out, don't prune),
keep only a tiny usage-hot set in RAM, and compute the rare stuff on demand.** Every layer scales to zero when idle.
Cost then tracks real query traffic, not the 100M-row corpus. This is the same "tier by real-world usage" law from
the cost analysis, realized with 2026 serverless products that did not exist a year ago.

## 1. The 2026 shift that makes this cheap (why it's different now)

- **Amazon S3 Vectors (GA Jan 2026):** native vector storage IN S3 — up to 2B vectors/index, 100 ms queries, 14
  regions, **fully serverless (no clusters/pods/shards), pay for storage + query, no idle compute, ~90% cost
  reduction vs hot vector DBs.** "Storage-first." Vectors live in cheap object storage and are queried serverlessly.
- **Turbopuffer:** serverless vector+FTS on object storage — **$0.02/GB storage, $1/PB queried; 100M–1B vectors ≈
  $500–2,000/mo** (vs $5–20k on Pinecone Serverless). Pure usage billing.
- **LanceDB:** S3-backed, storage/compute separated, **scale-to-zero query containers (2→200→0), you pay only for
  what you SCAN; compute scales with query load, not data size** (10 TB served by one small node off-peak).
- **Neon serverless Postgres:** **scale-to-zero** (pauses after idle, resumes in ms), autoscaling CU min/max,
  **pgvector included free**, $0.35/GB storage, pay-per-use with no minimums.
- **Modal (serverless GPU):** per-second billing, **scale-to-zero (pay $0 idle)** — on-demand strong-model/GPU
  embedding + rerank batches; H100 ~$3.95/hr only while running.

## 2. The stack (managed serverless primitives — do NOT build these)

| Layer | Managed serverless choice | Why | Cost shape |
|---|---|---|---|
| **Vector storage + query** | **Amazon S3 Vectors** (primary) · Turbopuffer (pay-per-query alt) · LanceDB (embedded/edge) | store ALL models/facets/reps cold; query serverlessly; ~90% cheaper; scale-to-zero | $0.02/GB store + per-query; idle $0 |
| **Registry / contracts / edges / receipts** | **Neon** serverless Postgres + pgvector | scale-to-zero, ms resume, pgvector free; hot-set index lives here | pay-per-CU-hour; idle ~$0 |
| **Compute: embed / rerank / build / graph-solve** | **Modal** (GPU, scale-to-zero) + **Cloud Run** (stateless API/router, scale-to-zero) | on-demand strong-model embedding; the linker/router runs stateless | per-second; idle $0 |
| **Bodies / descriptions / raw source** | **S3** standard + Glacier cold | the bulk text/code — cheapest tier | $0.023/GB hot, $0.004 cold |
| **Telemetry / outcome warehouse** | **DuckDB/MotherDuck over Parquet in S3** (or ClickHouse Cloud) | query the usage ledger + receipts serverlessly | pay-per-scan |
| **Hot cache / session alias table** | **Upstash Redis** / Cloudflare KV (serverless) | per-request billing | pay-per-request |

## 3. The tiering (build all · keep all · hot only what's used)

```
COLD (default, everything)   S3 Vectors: ALL models × ALL facets × ALL reps, quantized (int8/binary/PQ). $0.02/GB.
                             Queried serverlessly per request. This is the "build out everything, don't prune" tier.
        ↑ promote (usage ledger says this primitive/model is hot)     ↓ demote (unused)
HOT (tiny, usage-driven)     Neon pgvector / small Qdrant: the top-queried ~1–5% primitives × the champion model,
                             in RAM for sub-10ms. Promoted BY THE USAGE LEDGER, not lab guessing.
ON-DEMAND (rare)             Modal: embed a rare description/model AT QUERY TIME (never stored). Scale-to-zero.
```
- **Nothing is deleted** — cold ≠ gone. A representation the usage ledger never touches just stays cold ($0.02/GB)
  or is computed on demand. This is how "build out every model/facet/scorer" stays affordable.
- **The router promotes/demotes by real traffic** (`primitive_usage_ledger` + `linker_scoring_zoo.train_weights`):
  the hot set is whatever real prompts actually hit. Direction from lab tests; PRIORITY from production.

## 4. The retrieval path on this stack (same logic, serverless substrate)

```
query → Cloud Run router (stateless, autoscale)
   → HOT check (Neon pgvector, tiny)                         [ms, most repeat traffic served here / cache]
   → COLD recall (S3 Vectors: cheap model2vec lane)          [serverless, ~100ms, pay-per-query]
   → shortlist → STRONG rerank (Modal: BGE/Gemma/ColBERT on demand)  [GPU scale-to-zero, paid on K items]
   → multi-method scorers (linker_scoring_zoo, in-router)    [CPU, free-ish]
   → typed blockers + graph solve + assemble (our custom moat) → verify
   → log to usage ledger (Parquet/S3) → promotes tomorrow's hot set
```
Idle cost ≈ $0 (everything scales to zero). Busy cost = queries × per-query rate + Modal GPU-seconds. **Cost tracks
usage, not the 100M corpus.**

## 5. Managed vs custom — the split (the owner's question)

- **MANAGED serverless (buy, don't build):** vector storage+query (S3 Vectors/Turbopuffer), Postgres (Neon), GPU
  compute (Modal), object storage (S3), cache (Upstash), warehouse (MotherDuck). These are commodity + already
  autoscale/scale-to-zero. Building a custom vector DB in 2026 is wasted effort — S3 Vectors/Turbopuffer solved it.
- **CUSTOM (build — this IS the moat, and it's THIN + stateless):** the semantic ABI + evidence/compatibility graph;
  the multi-model / multi-scorer ROUTER + RRF fusion; the usage-driven TIERING/hot-promotion policy; the LINKER
  (resolve/assemble/typed-port blockers); the coverage ratchet + usage ledger. All of this is the code already built
  in `scripts/` — it runs stateless on Cloud Run/Modal over the managed data layers.
- **So: managed autoscaling + a thin custom control plane.** Not a custom database, not custom autoscaling infra —
  the managed primitives autoscale; our custom layer is the intelligence on top.

## 6. Cost at 100M on this stack (vs always-hot)

- **Storage (cold, everything):** even 100M × several models × quantized ≈ a few TB in S3 Vectors ≈ **$hundreds/mo**
  (and ~90% below hot vector DBs). Build-out stays affordable BECAUSE it's cold object storage.
- **Query:** pay-per-query — **scales with real traffic**, near $0 when idle. A moderate prod load ≈ **$100s–low-$1000s/mo**.
- **Compute:** Modal/Cloud Run scale-to-zero — **$0 idle**, GPU-seconds only during embedding/rerank bursts.
- **Postgres (Neon):** scale-to-zero — **$0 idle**, pennies-to-$100s under load.
- **Net:** **~$0 at idle; low-$100s to low-$1000s/mo under real load** — vs $1.5–5k/mo always-on. AND it keeps
  100% of the flexibility (every model/facet/rep stored cold, any of them queryable, new ones added anytime).

## 7. Migration path (small — the local build already maps here)

1. The local artifacts (facet store, per-model stores, packs) map 1:1 to **S3 Vectors buckets** (one index per
   model/facet-lane). `architecture/storage_tier_policy.json` already stubs the local→cloud swap as config-only.
2. Registry/edges/receipts → **Neon** (the `db/postgres/schema.sql` already exists).
3. The linker/router/minters (`scripts/*`) run as **Cloud Run** services + **Modal** functions — stateless over the
   managed layers. The MCP server + website are the same code behind a serverless endpoint.
4. Autoscaling is INHERITED from the managed primitives (S3 Vectors, Neon, Modal, Cloud Run all scale-to-zero /
   autoscale). No custom autoscaler to build.

**Bottom line:** run everything COLD in object storage (S3 Vectors, $0.02/GB — build out every model/rep, delete
nothing), keep a tiny usage-hot set in RAM, compute rare stuff on demand, and let managed serverless primitives
autoscale to zero. Full flexibility + expandability, ~$0 idle, cost that tracks real usage — with a thin custom
control plane (our linker + router + tiering policy) as the only thing we build.

## Sources
- Amazon S3 Vectors GA: https://aws.amazon.com/blogs/aws/amazon-s3-vectors-now-generally-available-with-increased-scale-and-performance/ · https://www.infoq.com/news/2026/01/aws-s3-vectors-ga/ · https://venturebeat.com/data-infrastructure/aws-claims-90-vector-cost-savings-with-s3-vectors-ga-calls-it-complementary
- Turbopuffer: https://turbopuffer.com/ · https://www.usagepricing.com/blueprint/turbopuffer
- LanceDB on S3 (scale-to-zero): https://aws.amazon.com/blogs/architecture/a-scalable-elastic-database-and-search-solution-for-1b-vectors-built-on-lancedb-and-amazon-s3/ · https://docs.lancedb.com/storage
- Neon serverless Postgres + pgvector: https://neon.com/pricing
- Modal serverless GPU (scale-to-zero): https://modal.com/blog/truly-serverless-gpus
