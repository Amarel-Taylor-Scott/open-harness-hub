# Vectorized Registry Hosting — 2026 Cost and Architecture Guide

This document extends [`low-cost-hosting-plan.md`](low-cost-hosting-plan.md) and
[`hybrid-postgres-bigquery-hosting.md`](hybrid-postgres-bigquery-hosting.md) with
concrete 2026 pricing and a phased plan specific to the billion-component, fully-vectorized
goal described in [`../codex/billion-component-goal.md`](../codex/billion-component-goal.md).

Do not duplicate infrastructure principles covered in those files. This document addresses:
what to host where at each vector-count tier, the pgvector-vs-dedicated-vector-DB decision
point, the multi-embedding/multi-dimension storage implication, and the cheapest starting shape.

All prices are approximate as of May 2026 and will drift. Treat them as order-of-magnitude
guides, not billing commitments. Citations are in the Sources section.

---

## 1. The Storage Problem This Addresses

The billion-component goal mandates that **every promoted component carries a real embedding
and is reachable by hybrid search** (keyword + vector + graph + facet). One object typically
needs multiple embeddings of different dimensions:

- a dense semantic vector (e.g. 768-d or 1536-d) for similarity search;
- a sparse vector (e.g. SPLADE or BM25) for keyword-style recall;
- a smaller compressed vector (e.g. 256-d binary-quantized) for fast pre-filter;
- optionally a multimodal vector when the component carries media.

A single canonical component therefore becomes one row in the relational registry and
**two to five vector rows** of varying dimensions. At a billion components, that is
2–5 billion individual vectors spread across multiple dimensionality spaces. No single
index can hold them all in one flat namespace; the architecture must route by model + dimension.

---

## 2. Pricing Reference (May 2026)

### 2a. Managed Postgres + pgvector

| Provider | Free tier | First paid shape | Storage | Notes |
|---|---|---|---|---|
| **Neon** (Databricks-owned) | 100 CU-h/mo, 0.5 GB | Launch: $0.106/CU-h, $0.35/GB-mo | $0.35/GB-mo (first 50 GB); $0.15/GB-mo beyond | Scale to zero; pgvector on all plans; 30 GB working DB runs ~$20–40/mo active |
| **Supabase** | 500 MB DB, 50 K MAU | Pro: $25/mo (8 GB, 100 K MAU) | Included up to plan limit | pgvector free on all plans; at 8 GB DB + heavy queries add compute add-ons |
| **RDS / Aurora Serverless v2** | None | db.r6g.large ~$100/mo | $0.115/GB-mo (gp3) | Most expensive; best compliance/isolation story; pgvector GA on Aurora |

For **50 M vectors at 768 dims** (approximately 150 GB of raw float32 data before HNSW
overhead), Neon or Supabase are cost-viable only if HNSW fits in RAM or you accept
slower disk-based traversal. At that scale a Neon Launch instance with 16 GB RAM costs
roughly $80–120/mo compute + $52/mo storage, but HNSW build time and cold-start
latency become real concerns.

### 2b. Dedicated Vector Databases (Managed Cloud)

| Provider | Free tier | 10 M vectors / mo est. | 100 M vectors / mo est. | Multi-dim support |
|---|---|---|---|---|
| **Qdrant Cloud** | 1 GB RAM, 4 GB disk | $120–180/mo | $2,800–5,500/mo | Named vectors: each point can carry multiple named vector spaces with different dims |
| **Weaviate Cloud** | 14-day trial, then $45+/mo | $200–400/mo | ~$5,000–10,000/mo | Named vectors; charges per million vector-dimensions stored |
| **Zilliz Cloud (Milvus)** | Serverless free tier | $65–200/mo | $3,200–6,500/mo | Multiple vector fields per collection with different dims; tiered storage cuts cost 87% |
| **Pinecone** | Serverless free | $70–150/mo | $7,000–28,000/mo | Separate indexes per model/dim; no native multi-dim per point |

Qdrant's **named vectors** feature is the most mature multi-embedding solution: a single
point stores a "text" vector (768-d), an "image" vector (1024-d), and a "compressed"
vector (256-d binary-quantized) in one record. Weaviate has a similar feature. Pinecone
requires separate indexes per model, which multiplies index cost.

Milvus 2.6 (GA on Zilliz Cloud as of early 2026) introduced a multi-layer storage
architecture that places hot vectors in memory, warm vectors on local SSD, and cold vectors
in object storage — reducing storage cost by up to 87% at billion scale while holding
sub-10 ms latency for the hot tier.

### 2c. Cheap Compute for Workers

| Provider | Entry shape | Entry price | Best use |
|---|---|---|---|
| **Render** | 512 MB / 0.5 vCPU | $7/mo per service | API gateway, light workers, admin dashboard |
| **Fly.io** | Pay-as-you-go | From ~$2/mo | Containerized edge workers, bursty tasks |
| **Google Cloud Run** | Per-request billing | $0.024/1K vCPU-s (Tier 1); 2M req/mo free | Embedding jobs, isolation-sensitive workers, browser automation |
| **Hetzner Cloud** | CAX11 ARM (2 vCPU, 4 GB) | ~$3.79/mo (post Apr 2026 increase) | Persistent background workers, self-hosted vector DB nodes; European DC |
| **Hetzner Dedicated** | AX41-NVMe | ~$35–60/mo (post-April increase ~+30%) | GPU-adjacent, heavy batch embedding, self-hosted Qdrant/Milvus nodes |

Hetzner raised prices ~30–37% from April 1, 2026, citing hardware and energy costs.
Even after the increase, their ARM CAX-series and dedicated AX-series remain among the
cheapest raw compute per GB-hour in any EU data center.

Cloud Run is the best fit for bursty embedding jobs: you pay only for active vCPU-seconds,
with 180 K vCPU-seconds free per month. A batch embedding job that runs 2 hours/day on
2 vCPUs costs roughly $3.46/mo in Tier 1 regions.

### 2d. Object Storage

| Provider | Storage | Egress | Notes |
|---|---|---|---|
| **Cloudflare R2** | $0.015/GB-mo | $0 (zero egress fees) | Best for high-read JSONL shards and catalog exports |
| **Backblaze B2** | $0.006/GB-mo | Free up to 3× monthly storage, then $0.01/GB | Cheapest raw storage; B2-Cloudflare peering = zero egress via CDN |
| **AWS S3 Standard** | $0.023/GB-mo | $0.09/GB | Most ecosystem compatibility; expensive egress |
| **GCS Standard** | $0.020/GB-mo | $0.12/GB | Good if already on GCP (Cloud Run synergy) |

For 10 TB of JSONL staging shards and catalog exports, R2 costs ~$150/mo with no egress
bill. Backblaze B2 costs ~$60/mo for the same data and is effectively zero-egress when
delivered through Cloudflare's network.

### 2e. Queue / Async

| Provider | Model | Free | Cost at scale |
|---|---|---|---|
| **Upstash Redis** | $0.20/100 K commands | 500 K commands/mo | Predictable; $10–50/mo for typical ingest queues |
| **Upstash QStash** | $1/100 K messages | Included | Good for delayed/scheduled embedding jobs |
| **Render Redis** | Add-on | None | Simple if already on Render; limited control |
| **Cloud Tasks (GCP)** | Per task | 1 M free/mo | Best pairing with Cloud Run workers |

---

## 3. The pgvector-vs-Dedicated-Vector-DB Decision Point

### When pgvector is enough

pgvector is the right choice when:
- the promoted component count is below ~20 M and embedding dimensions are 768 or fewer;
- the team already runs Postgres for the relational registry (shared operational store);
- the query pattern is predominantly filtered (good Postgres indexes suppress the vector
  scan to a manageable candidate set);
- read traffic is moderate and connection pooling (PgBouncer or Supabase's pooler) is not
  yet saturated.

At 10 M vectors of 768 dims, a Neon or Supabase instance with 16–32 GB RAM can hold the
HNSW index in memory and serve sub-50 ms queries. Cost: roughly $80–150/mo all-in.

### The wall: HNSW memory math

HNSW index memory grows as approximately:

```
index_bytes ≈ N × D × 4 × 2.5
```

where N = number of vectors, D = dimensions, 4 bytes per float32, and 2.5× for graph
overhead. With half-precision (float16) or scalar quantization, divide by 2.

| Vectors | Dims | Approx HNSW RAM (float32) | Approx HNSW RAM (float16) |
|---|---|---|---|
| 10 M | 768 | ~80 GB | ~40 GB |
| 50 M | 768 | ~400 GB | ~200 GB |
| 100 M | 768 | ~800 GB | ~400 GB |
| 100 M | 1536 | ~1,600 GB | ~800 GB |

Beyond ~50 M vectors, keeping the full HNSW graph hot in RAM on managed Postgres
requires very large (and expensive) instances. At that point query latency degrades
to multi-second disk traversal if the graph falls out of cache, which makes pgvector
inappropriate for interactive search.

### The graduation threshold: ~50 M vectors (or earlier with multi-dim)

Move from pgvector to a dedicated vector database when **any** of:
- total promoted vectors (across all embedding models) exceeds 50 M;
- you need sub-100 ms search across the full promoted corpus without massive RAM;
- you carry 3+ named embedding spaces per object (multi-dim requirement pushes the
  effective vector count 3–5× above the component count);
- write throughput to the vector index exceeds ~5 K vectors/sec sustained;
- you need horizontal sharding (pgvector has no native shard; Qdrant and Milvus do).

For Open Harness Hub at T2 (100 M components, each with 2–3 embeddings = 200–300 M
vectors), **pgvector alone is not viable**. The architecture must graduate to a dedicated
vector engine.

### Multi-embedding / multi-dimension storage

Each component row in the relational registry maps to multiple `object_embedding` rows
with different `model_id` and `dimension` values. The vector DB must store all of them
without merging the spaces. Options:

| Approach | How | Works at scale? |
|---|---|---|
| **Qdrant named vectors** | One collection, multiple named vector fields per point; each field has its own dim and metric | Yes — the recommended path; no extra cost per named space |
| **Weaviate named vectors** | Same concept; charges per million dim-months | Yes — cost grows linearly with dim count |
| **Milvus multiple vector fields** | Schema-level; each field independent | Yes — Milvus 2.6 supports multi-vector natively |
| **Separate indexes per model** | One Pinecone/Qdrant index per model + dim combo | Works but multiplies index management; no shared payload |
| **pgvector with router** | Separate `object_embeddings` table per model + partition by `model_id` | Works up to ~20 M per model; no horizontal scale |

**Recommendation:** Use Qdrant named vectors or Milvus multi-vector fields as the dedicated
vector store at T2. Maintain the Postgres `object_embedding` table as the **source of
truth for row metadata** (model_id, dimension, source_content_hash, timestamp), and sync
only the vector data to the vector DB. The Postgres row wins on conflict.

---

## 4. Phased, Costed Plan by Tier

### Tier 0: Start Cheapest (0 → ~5 M vectors, ~5 K–500 K promoted components)

This is the daily-factory phase. The goal is to build and validate the full row-family
pipeline before paying for scale.

| Service | Provider | Shape | Approx monthly $ |
|---|---|---|---|
| Static catalog site | Cloudflare Pages | Free tier | $0 |
| Relational registry + pgvector | Neon Launch | 4–8 GB RAM, auto-suspend | $20–50 |
| Background workers (ingest, embed, validate) | Render (1 worker) | 1 GB / 0.5 vCPU | $7 |
| Burst embedding jobs | Cloud Run | 2 vCPU, 4 GB, runs 2 h/day | ~$3–5 |
| Object storage (JSONL shards, exports) | Cloudflare R2 | 500 GB | ~$8 |
| Queue | Upstash Redis | Pay-as-you-go | $0–10 |
| **Total** | | | **~$40–80/mo** |

At this tier pgvector handles all vector search. HNSW on 5 M vectors at 768 dims
requires ~40 GB RAM with float16, which exceeds a small Neon instance. Use IVFFlat
(lower RAM, slightly less precise) or limit to 2 M promoted vectors while staging the rest.
Scale the Neon instance to 8–16 GB when approaching 5 M active promoted vectors.

**Upgrade triggers from Tier 0:**
- pgvector query p95 latency exceeds 500 ms on unfiltered corpus search;
- promoted vector count (across all models) approaches 10 M;
- daily ingest exceeds what one Render worker can drain.

---

### Tier 1: Proven Floor (~1 M–10 M promoted components, ~3 M–30 M vectors)

All components vectorized and searchable; conversational builder in alpha.

| Service | Provider | Shape | Approx monthly $ |
|---|---|---|---|
| Static catalog site | Cloudflare Pages | Free | $0 |
| Relational registry + pgvector (hot search) | Neon Scale or Supabase Pro | 16–32 GB RAM | $80–180 |
| Worker fleet (ingest, OCR, dedupe) | Render (2 workers) or Fly.io | 2 GB / 1 vCPU each | $25–50 |
| Embedding batch workers | Cloud Run | Autoscale; ~4 h/day at 4 vCPU | $20–40 |
| Object storage | Cloudflare R2 | 2 TB (JSONL, CDC logs, exports) | $30 |
| Queue | Upstash Redis + QStash | Moderate traffic | $20–40 |
| Analytics (optional) | BigQuery on-demand | First 1 TB query/mo free | $0–20 |
| **Total** | | | **~$175–360/mo** |

pgvector remains the primary vector engine at this tier. The Postgres relational registry
(labels, review tickets, dedupe clusters, CDC events) and the vector index coexist in the
same managed instance. This minimizes operational complexity.

Maintain the `object_embedding` table with full metadata even at this tier — it is the
canonical record for every vector, regardless of where the actual float array lives later.

**Upgrade triggers from Tier 1:**
- total promoted vectors across all embedding models exceeds 30–50 M;
- HNSW index no longer fits in the instance's buffer pool and cold search latency spikes;
- write throughput to the vector index is queuing ingest jobs;
- conversational builder requires multi-model retrieval fusion in real time.

---

### Tier 2: Breadth (~100 M promoted components, ~200–500 M vectors)

Source-surface matrix automated; conversational builder in beta; dedupe at scale.

At this tier, pgvector alone cannot serve interactive search. Introduce a dedicated vector
engine alongside Postgres.

| Service | Provider | Shape | Approx monthly $ |
|---|---|---|---|
| Relational registry (metadata, labels, CDC) | Neon Scale or Supabase Pro (large) | 64 GB RAM, high-IOPS | $300–600 |
| Dedicated vector DB — hot search tier | Qdrant Cloud Standard or self-hosted on Hetzner | 3–6 nodes × 32 GB RAM | $800–2,000 |
| Dedicated vector DB — warm/archive tier | Milvus on Hetzner dedicated (self-hosted) or Zilliz tiered storage | — | $500–1,500 |
| Worker fleet | Cloud Run + Hetzner ARM (CAX21, 4 vCPU, 8 GB, ~$7/mo each) | 4–8 instances | $100–200 |
| Embedding GPU burst | Lambda Labs or RunPod spot | A10 GPU, ~$0.60/h, 4 h/day | $70 |
| Object storage | Cloudflare R2 + Backblaze B2 | R2 for hot exports; B2 for cold JSONL archive | $100–200 |
| Queue | Upstash Redis + QStash (scale plan) | — | $50–100 |
| Analytics / ranking | BigQuery on-demand | Offline ranking, telemetry | $50–150 |
| **Total** | | | **~$2,000–4,750/mo** |

**Architecture at Tier 2:**
- Postgres remains the relational source of truth. The `object_embedding` table records
  every vector's metadata (model_id, dim, source_hash, sync_timestamp). It does not store
  the float arrays in production — only the metadata.
- Qdrant (or Weaviate) holds the float arrays via named vectors: one Qdrant point per
  canonical component, with named vector fields for each embedding model. Filtering uses
  Qdrant payload indexes backed by the same metadata.
- Milvus handles the archive/bulk tier when Qdrant memory cost grows. Milvus 2.6 tiered
  storage places cold vectors in object storage (R2 or GCS) and only keeps hot vectors in
  RAM, reducing effective cost per vector by 50–87%.
- The conversational builder queries Qdrant for hybrid retrieval (dense + sparse named
  vectors), then fetches component metadata from Postgres to assemble the pipeline.

---

### Tier 3: Billion+ (~1 B components, ~2–5 B vectors)

Partitioned load + CDC at scale; cost ceiling held; builder eval passing.

At this tier, no single managed service holds all vectors. The architecture shards by
domain partition and embedding model. Operational cost discipline is critical: embedding
waste and over-provisioned RAM are the two largest cost drivers.

| Service | Provider | Shape | Approx monthly $ |
|---|---|---|---|
| Relational registry | RDS Aurora or self-hosted Postgres cluster | Multi-AZ, read replicas | $1,500–3,000 |
| Hot vector search (top-priority domains) | Qdrant Cloud Premium or Milvus on Kubernetes | 20+ nodes, quantization on | $8,000–20,000 |
| Warm vector search (lower-priority domains) | Self-hosted Milvus on Hetzner dedicated cluster | AX162-R or similar | $3,000–8,000 |
| Embedding GPU fleet | Hetzner GPU (GEX44/GEX130) or Lambda Labs reserved | 4–8 A100 40 GB equiv. | $2,000–5,000 |
| Object storage (cold vectors + JSONL archive) | Backblaze B2 + Cloudflare R2 CDN | 50–100 TB | $300–800 |
| Queue + CDC bus | Upstash + managed Kafka (Confluent Serverless or Redpanda Cloud) | — | $300–600 |
| Analytics + offline ranking | BigQuery or ClickHouse Cloud | Vector search, ranking, telemetry | $500–1,500 |
| **Total** | | | **~$16,000–39,000/mo** |

Cost control at this tier is dominated by three levers:
1. **Quantization.** Binary quantization reduces vector RAM by 32×; scalar quantization
   reduces by 4×. Apply to any embedding not in the top-10% query-frequency tier. Milvus
   and Qdrant both support on-the-fly quantization; the relational metadata row records
   the quantization method alongside the model_id.
2. **Tiered eviction.** Move vectors for components with zero search hits in the last 90
   days to cold object storage (B2 or R2). Milvus tiered storage handles this automatically
   when configured.
3. **Embedding batching discipline.** Never embed individual draft candidates in real time.
   Batch embed on a schedule; write to JSONL staging first; load to the vector DB after
   promotion approval. This prevents orphan float arrays from filling the hot tier.

---

## 5. Start Cheapest: Recommended Initial Shape

For the daily factory phase (today through ~500 K promoted components):

```
Cloudflare Pages (static catalog, $0)
  +
Neon Launch or Supabase Pro (Postgres + pgvector, $20–50/mo)
  +
One Render background worker (ingest + embedding jobs, $7/mo)
  +
Cloud Run burst (heavy embedding batches, ~$5/mo)
  +
Cloudflare R2 (JSONL shards + exports, ~$5–15/mo)
  +
Upstash Redis (queue, $0–10/mo)

Total: $37–87/mo
```

This shape matches Phase 1 of `low-cost-hosting-plan.md` exactly. Nothing changes about
that recommendation; this document adds the forward-looking decision tree for when vector
scale forces a change.

**Do not pre-buy dedicated vector infrastructure.** The daily factory must first prove it
can generate, dedupe, embed, and promote components at the T1 rate. Spinning up Qdrant or
Milvus before the promoted corpus reaches 10 M vectors is premature and adds operational
overhead that slows factory velocity.

### Upgrade trigger checklist

Use this checklist to decide when to graduate to the next tier:

- [ ] pgvector p95 search latency > 500 ms on the promoted corpus (unfiltered)
- [ ] HNSW index size > 80% of available instance RAM (check `pg_relation_size`)
- [ ] Daily promoted vector count growing faster than RAM headroom allows
- [ ] Multi-model retrieval fusion needed in real time (2+ embedding spaces per query)
- [ ] Worker queue depth consistently > 10 K pending embedding jobs
- [ ] Monthly Postgres compute bill exceeds $300 (usually means a dedicated vector engine
  would be cheaper per query at that point)

---

## 6. Summary Decision Matrix

| Promoted vector count | Recommended vector store | Rough monthly infra $ | Key risk |
|---|---|---|---|
| 0 – 10 M | pgvector (Neon/Supabase) | $40–180 | HNSW RAM ceiling; mitigate with IVFFlat or quantization |
| 10 M – 50 M | pgvector (large instance) or Qdrant Cloud entry | $150–500 | Index build time; cold-start on serverless |
| 50 M – 300 M | Qdrant Cloud Standard + Postgres metadata | $1,000–5,000 | Named-vector sync complexity; CDC lag |
| 300 M – 2 B | Milvus tiered + Qdrant hot shard + Postgres | $5,000–20,000 | Embedding waste, quantization tuning, sharding |
| 2 B+ | Distributed Milvus / Qdrant cluster + cold object storage | $15,000–40,000+ | Cost ceiling discipline; GPU fleet sizing |

---

## 7. Sources

- [Neon Serverless Postgres Pricing 2026 — Simplyblock/Vela](https://vela.simplyblock.io/articles/neon-serverless-postgres-pricing-2026/)
- [Neon Pricing page](https://neon.com/pricing)
- [Supabase Pricing & Fees](https://supabase.com/pricing)
- [Supabase Vector module](https://supabase.com/modules/vector)
- [Supabase vs pgvector — Markaicode](https://markaicode.com/vs/supabase-vs-pgvector/)
- [Qdrant Pricing page](https://qdrant.tech/pricing/)
- [Qdrant Billing & Payments docs](https://qdrant.tech/documentation/cloud-pricing-payments/)
- [Qdrant Cloud Pricing 2026 — LeanOps](https://leanopstech.com/blog/qdrant-cloud-pricing-2026/)
- [Qdrant Cloud Pricing 2026 — Ranksquire](https://ranksquire.com/2026/04/19/qdrant-cloud-pricing-2026/)
- [Storing multiple vectors per object in Qdrant — Qdrant article](https://qdrant.tech/articles/storing-multiple-vectors-per-object-in-qdrant/)
- [Qdrant Named Vectors documentation](https://qdrant.tech/documentation/manage-data/vectors/)
- [Weaviate Pricing page](https://weaviate.io/pricing)
- [Weaviate Cloud Pricing 2026 — Ranksquire](https://ranksquire.com/2026/04/22/weaviate-cloud-pricing-2026/)
- [Weaviate Pricing 2026 — CostBench](https://costbench.com/software/vector-databases/weaviate/)
- [Milvus 2.6 introduction — Milvus Blog](https://milvus.io/blog/introduce-milvus-2-6-built-for-scale-designed-to-reduce-costs.md)
- [Zilliz Cloud GA of Milvus 2.6.x — PR Newswire](https://www.prnewswire.com/news-releases/zilliz-announces-general-availability-of-milvus-2-6-x-on-zilliz-cloud-powering-billion-scale-vector-search-at-even-lower-cost-302665829.html)
- [Milvus & Zilliz Cloud Pricing 2026 — LeanOps](https://leanopstech.com/blog/milvus-zilliz-cloud-pricing-2026/)
- [Zilliz Cloud Pricing page](https://zilliz.com/pricing)
- [pgvector vs Qdrant vs Weaviate at 100 M vectors — Elest.io](https://blog.elest.io/pgvector-vs-qdrant-vs-weaviate-which-vector-database-holds-up-at-100m-vectors/)
- [Vector Database Cost Comparison 2026 — LeanOps](https://leanopstech.com/blog/vector-database-cost-comparison-2026/)
- [Pinecone vs Weaviate vs Qdrant vs pgvector 2026 — Second Talent](https://www.secondtalent.com/resources/pinecone-vs-weaviate-vs-qdrant-vs-pgvector/)
- [Best Vector Databases 2026 — Encore](https://encore.dev/articles/best-vector-databases)
- [Vector Database Performance: pgvector vs Pinecone vs Qdrant vs Weaviate — Vecstore](https://vecstore.app/blog/vector-database-performance-compared)
- [Scaling pgvector: Memory, Quantization, and Index Build — DEV Community](https://dev.to/philip_mcclarence_2ef9475/scaling-pgvector-memory-quantization-and-index-build-strategies-8m2)
- [pgvector DBA guide Part 2: Indexes (March 2026) — dbi-services](https://www.dbi-services.com/blog/pgvector-a-guide-for-dba-part-2-indexes-update-march-2026/)
- [HNSW Indexes with Postgres and pgvector — Crunchy Data](https://www.crunchydata.com/blog/hnsw-indexes-with-postgres-and-pgvector)
- [pgvector 30× faster index build — Neon Blog](https://neon.com/blog/pgvector-30x-faster-index-build-for-your-vector-embeddings)
- [Cloudflare R2 Pricing docs](https://developers.cloudflare.com/r2/pricing/)
- [Cloudflare R2 Pricing 2026 — LeanOps](https://leanopstech.com/blog/cloudflare-r2-pricing-2026/)
- [Backblaze B2 Pricing 2026 — LeanOps](https://leanopstech.com/blog/backblaze-b2-pricing-2026/)
- [Render Pricing page](https://render.com/pricing)
- [Render Pricing 2026 — CostBench](https://costbench.com/software/developer-tools/render/)
- [Fly.io Pricing 2026 — Toolradar](https://toolradar.com/tools/flyio/pricing)
- [Google Cloud Run Pricing docs](https://cloud.google.com/run/pricing)
- [Hetzner Price Adjustment April 2026 — igors LAB](https://www.igorslab.de/en/hetzner-to-significantly-increase-prices-for-cloud-and-dedicated-servers-from-april-2026/)
- [Hetzner Statement on price adjustment April 2026](https://www.hetzner.com/pressroom/statement-price-adjustment/)
- [Hetzner Cloud Review 2026 — Better Stack](https://betterstack.com/community/guides/web-servers/hetzner-cloud-review/)
- [Upstash Redis Pricing docs](https://upstash.com/docs/redis/overall/pricing)
- [Upstash Pricing page](https://upstash.com/pricing)
- [Vector DB Costs 2026: Pinecone vs Weaviate vs Qdrant — LeanOps](https://leanopstech.com/blog/vector-database-cost-comparison-2026/)
- [Amazon Aurora vs Neon serverless Postgres cost comparison — Vantage](https://www.vantage.sh/blog/neon-vs-aws-aurora-serverless-postgres-cost-scale-to-zero)
- [Milvus Cost Optimization: Cut Vector Database Costs by Up to 80% — Milvus Blog](https://milvus.io/blog/how-to-cut-vector-database-costs-by-up-to-80-a-practical-milvus-optimization-guide.md)
