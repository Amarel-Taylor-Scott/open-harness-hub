# Low-Cost Hosting Plan

The cheapest useful architecture should start simple, then split services only when a bottleneck appears.

## MVP Stack

For fast launch, use:

- **Static site**: GitHub Pages, Cloudflare Pages, Netlify, or Vercel.
- **API and workers**: Render web service plus Render background worker, or Cloud Run when container scaling matters.
- **Database**: Postgres with pgvector.
- **Auth and payments**: Supabase Auth or a lightweight app auth provider plus Stripe.
- **Object storage**: Cloudflare R2, S3, GCS, or Supabase Storage.
- **Queue**: Redis, Upstash, Render Redis, or Cloud Tasks.
- **Search**: Postgres full-text search and pgvector first.
- **Analytics/cost traces**: Postgres first, BigQuery or ClickHouse later.

This keeps the first deploy understandable: one app, one database, one worker, one object bucket.

Use `infra/postgres/docker-compose.pgvector.yml` for local pgvector development and the same `db/postgres/schema.sql` / loader SQL / `db/postgres/object_count_report.sql` sequence for Render or managed Postgres.

For object generation, start with one queue and one worker process that can run source ingest, Markdown conversion, sensitive-data screening, LLM polishing, verification, labeling, dedupe, and index emission. Split the worker only after runtime dependencies or queue latency force the issue.

## When to Use Render

Render is a good default for quick SaaS validation:

- fast web service and worker deployment;
- simple Postgres and Redis add-ons;
- easy environment variables and preview deploys;
- fewer moving parts than a full GCP/AWS setup.

Use Render for:

- API gateway;
- blueprint generation service;
- background source scans;
- embedding jobs at low to medium volume;
- small admin dashboards.

Do not overload Render with large vector search, high-volume crawling, or heavy GPU/media workloads. Treat those as pluggable workers.

## When to Add Cloud Functions or Cloud Run

Use dedicated serverless/container runtimes for:

- source scans that need isolation;
- web archive capture workers;
- browser automation workers;
- page-to-Markdown and PDF/document conversion workers;
- sensitive-data gates that must run in a tenant boundary;
- LLM polish and verification workers with custom model endpoints or bring-your-own-key routing;
- model pricing refresh jobs;
- cloud-provider pricing lookup;
- per-tenant custom tools;
- long-running workflow import scans;
- bursty embedding jobs;
- containerized search adapters.

Cloud Run is a strong fit when the tool needs a container image, custom dependencies, browser automation, or predictable request isolation. Cloud Functions are better for smaller event handlers.

## When to Add BigQuery

Postgres should be enough for early product data. Add BigQuery, ClickHouse, or another warehouse when you need:

- large telemetry queries;
- cost traces across many runs;
- search analytics;
- usage/rating aggregation;
- billing event reconciliation;
- offline primitive ranking jobs;
- long-term audit analytics.

Do not put the transactional primitive registry only in BigQuery. Use it as an analytics and batch-ranking layer.

For the million-object path, prefer the hybrid plan in
[`hybrid-postgres-bigquery-hosting.md`](hybrid-postgres-bigquery-hosting.md):
Postgres/pgvector remains the hot operational store, object storage holds raw
and replayable shards, and BigQuery handles cold analytics, vector experiments,
ranking, telemetry, and trajectory-fragment cache economics.

## Search Evolution

Start:

- Postgres FTS for keyword;
- pgvector for semantic search;
- JSONB metadata filters;
- trigram indexes for fuzzy matching.

Next:

- Qdrant or Weaviate for large vector collections;
- Meilisearch, Typesense, or OpenSearch for keyword/facet search;
- Neo4j, Apache AGE, or a graph index for dependency/entity exploration;
- BigQuery or ClickHouse for offline ranking and telemetry.

## Cost Control Rules

- Batch embeddings; do not embed every draft immediately.
- Prefer local or cheap embedding models for low-risk objects.
- Store raw snapshots in cheap object storage, not Postgres.
- Keep only canonical metadata and index records in Postgres.
- Use queues and rate limits for source scans.
- Cache pricing, search, and blueprint responses with snapshot IDs.
- Run expensive LLM polishing only after cheap filters and dedupe.
- Redact or block sensitive content before external model calls.
- Record model route, prompt version, pricing snapshot, worker image, and source span ids for every polished object.
- Route high-volume objects into JSONL packs before making individual manifests.

## Suggested Phases

### Phase 1: Static + Render + Postgres

Launch a searchable SaaS prototype with login, basic search, blueprint generation, and admin ingestion.

### Phase 2: Worker Split

Move source scanning, archive lookup, page-to-Markdown conversion, privacy gates, embeddings, LLM polishing, verification, and workflow import into separate workers or Cloud Run services.

### Phase 3: Search Split

Add specialized vector and keyword engines when Postgres search becomes the bottleneck.

### Phase 4: Warehouse

Add BigQuery or ClickHouse for usage telemetry, ranking, cost traces, and large-scale source analytics.

### Phase 5: Multi-Tenant Marketplace

Add signed publishers, payments, private tenant registries, ratings, eval dashboards, MCP setup, Terraform generation, and deployment blueprints.
