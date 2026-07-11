# Best Setup Per Component + The Scale-Up Path (researched 2026-07-10)

> Owner ask: "get me the best possible setup for all components and a scale-up path if we need." This REFINES
> `docs/CLOUD-ARCHITECTURE-SERVERLESS-TIERED.md` for the Fly-first reality (owner provides a Fly.io token) and
> updates it with 2026 GA/pricing facts (S3 Vectors GA · Turbopuffer price cuts · Fly GPU deprecation · ParadeDB
> state · LanceDB maturity). Multi-path law applies: every row below is an ACTIVE DEFAULT with labelled raced
> alternates — receipts pick winners, prose never does. All $ figures are researched estimates, not measurements.

## The one architectural invariant

Our retrieval intelligence lives ABOVE the store (fusion zoos, LSH band keys, facet router, learned weights,
waterfall). Every mechanism — LSH blocking, hybrid lexical+dense, multivectors, heuristics — is app-side and
backend-agnostic, so each storage row below is swappable by config (`architecture/storage_tier_policy.json`),
never by rewrite. The adaptive-vectorization waterfall bounds vector spend at every stage: logical catalog
uncapped, physical vectors usage-earned.

## V1 — NOW (shipped, ~$10–15/mo, single region)

| Component | Default (proven) | Notes |
|---|---|---|
| App + MCP + agent API | Fly machine (2GB) — `capability_saas_gateway` container | proven in-container 2026-07-10; scale-to-zero |
| Corpus + lexical index | in-image (128M governed index + 362M cards), SQLite sidecars | O(candidates) pruned search, 130,385 docs |
| Tenant state (identity/receipts/ledgers) | Fly volume `/data` | hashes only; append-only receipts |
| Embeddings | in-process (model2vec ~2.3s/112K, fastembed ONNX) | no GPU needed |
| Billing | billing_ledger/billing_plane drafts; Stripe seam inert until `STRIPE_API_KEY` | pricing DRAFT, owner-confirmable |
| Deploy | `build_capability_saas_bundle.py --deploy` (FLY_API_TOKEN) | GH Actions workflow in bundle |

**Move to V2 when:** >~1K searches/day sustained, >3 paying tenants, weekly corpus rebuilds, or a second region.

## V2 — GROWTH (~$100–200/mo)

| Component | Default | Raced alternates | Why |
|---|---|---|---|
| App | Fly ×2 machines (HA) | Railway (official MCP server — most agent-drivable alternate), Render, Cloud Run | bundle is a plain Dockerfile; ports unchanged |
| Cold objects (bodies/cards/corpus) | **Tigris** (Fly-native S3; `fly storage create`; shadow-bucket lazy migration from/to any S3) | Cloudflare R2, AWS S3 | zero-egress-drama, in-platform |
| Hot relational + filtered vectors | **Fly Managed Postgres + pgvector** (Vector/PostGIS click-enable; extension list is otherwise NARROW — core FTS is built-in, pg_trgm is not offered) | Neon (scale-to-zero, branching; dropped pg_search 2026-03), unmanaged postgres-flex (any extension) | tenants/plans/receipts/blockers + hot vector set co-located; filtered ANN in SQL |
| Cold vectors (serverless) | **LanceDB embedded over Tigris** — file-based, in-process with the gateway, multivector, AWS-endorsed at 1B+ | **Turbopuffer** ($64/mo Launch min; $0.02/GB; $1/PB queried post-2026-02 cuts) | pay-per-query economics; no extra always-on service |
| Lexical | our persisted pruned index (primary) | **ParadeDB pg_search** (Tantivy BM25 + pgvector RRF hybrid in ONE SQL query; self-host image — Neon dropped it) — race when BM25-in-SQL is wanted | our index is proven; BM25-in-DB is a receipt away |
| Cache / cross-machine rate limits | in-proc + volume | **Upstash Redis** (per-request billing, Fly partner) | needed only at ≥2 machines |
| Background jobs (waterfall apply, enrichment, rebuilds) | Fly worker process group in the same app | Upstash QStash | same bundle, second process |
| Embedding bursts | **Modal** (per-second GPU, scale-to-zero — already a RESOURCES row) | RunPod/Beam | **Fly GPUs are DEPRECATED as of 2026-07-31 — never build on them** |
| Observability | Fly metrics/logs + OTel export | Grafana Cloud free tier, Axiom | adopt-OTel was already on our list |

**Move to V3 when:** >5M promoted cards, >50 QPS sustained, p95 >300ms warm, multivector fan-out >100M physical
vectors, or a compliance/multi-region requirement.

## V3 — 100M+ SCALE (~$650–2,500/mo, cost tracks usage not corpus)

- **Cold vector store**: race **AWS S3 Vectors** (GA 2025-12: 2B vectors/index — 40× preview, 20T/bucket,
  sub-100ms, ~90% cheaper than specialized DBs, 14 regions) vs **Turbopuffer** (100M–1B @1536d ≈ $500–2K/mo;
  our 256–768d waterfall-bounded counts land far lower) vs LanceDB-on-Tigris scaled out. Keep all three as rows.
- **Hot filtered lane**: MPG pgvector while it holds; **pgvectorscale (DiskANN)** self-host when HNSW build
  RAM/time hurts; **Qdrant on Fly volumes** if named multivectors + payload-filter blocking in-store beat app-side.
- **Lexical at scale**: ParadeDB or OpenSearch raced against the sharded own-index.
- **Multi-region**: Fly regions + Tigris global caching + Postgres read replicas; receipts/ledgers per-region,
  reconciled (billing_ledger is already receipt-authoritative).
- **pgvector verdict (challenged, as directed)**: keep it ONLY as the hot filtered row. Its known strains at our
  scale — HNSW build cost ≥100M rows, churn bloat, the 9B-row facet fan-out shape, no MaxSim late-interaction,
  no pay-per-query idle-zero — are exactly what the cold serverless rows and the waterfall absorb.

## Component rows that never change across V1→V3

Identity (embedded, ours) · billing (receipts → ledger → draft invoices → Stripe seam) · the deterministic agent
tool + flexible MCP pair · the zoos (fusion/LSH/lexical-signal/router) · candidate/truth boundary
(`serves_truth=false` end to end) · deploy bundle (plain Dockerfile → portable to Railway/Render/Cloud Run
unchanged).

## Sources (2026-07-10)

Fly MPG + extensions: fly.io/docs/mpg, fly.io/docs/mpg/extensions · Tigris: fly.io/docs/tigris,
tigrisdata.com/docs/sdks/fly · Fly GPU deprecation (2026-07-31): community.fly.io/t/gpu-migration-fly-io-gpus-
will-be-deprecated-as-of-july-31-2026/27110 · S3 Vectors GA: aws.amazon.com/blogs/aws/amazon-s3-vectors-now-
generally-available-with-increased-scale-and-performance, infoq.com/news/2026/01/aws-s3-vectors-ga · Turbopuffer:
turbopuffer.com/pricing, usagepricing.com/blueprint/turbopuffer · ParadeDB: paradedb.com/blog/hybrid-search-in-
postgresql-the-missing-manual, neon.com/docs/extensions/pg_search (dropped for new projects 2026-03) · LanceDB:
aws.amazon.com/blogs/architecture/a-scalable-elastic-database-and-search-solution-for-1b-vectors-built-on-
lancedb-and-amazon-s3, lancedb.com · Hosting MCP landscape: docs.railway.com/ai/mcp-server,
mcpplaygroundonline.com/blog/deploy-mcp-server-vercel-railway-render-heroku-flyio.
