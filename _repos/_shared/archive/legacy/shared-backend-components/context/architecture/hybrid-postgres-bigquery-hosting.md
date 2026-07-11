# Hybrid Postgres and BigQuery Hosting

For the first product version, the cheapest useful shape is not "all BigQuery"
or "all Postgres." Use a hot/cold split.

## Recommendation

Use:

- Postgres plus pgvector for hot product state, API queries, tenant isolation,
  queue-visible object status, labels, review tickets, and first search;
- object storage for raw snapshots, JSONL shards, generated media, archived
  pages, exported CSV, and replayable load files;
- BigQuery for cold analytics, large scans, vector experiments, cost traces,
  ranking jobs, telemetry, and cross-run aggregate analysis;
- Cloud Run or container workers only for heavy tools, browsers, custom search
  runtimes, embedding batches, and tenant-isolated processors.

## Why Postgres First

Postgres is the simplest operational source of truth for the SaaS:

- ordinary relational joins over objects, labels, entities, reviews, users, and
  tenants;
- transactional updates for ingestion and review workflows;
- full-text search, JSONB filters, trigram/fuzzy search, and pgvector;
- easy local development with the repo's Docker Compose and schema;
- cheaper mental model for the first 1M rows.

Keep the application read/write path in Postgres until a measured workload says
otherwise.

## Why BigQuery Later

BigQuery becomes valuable when the workload is mostly append-only, analytic, or
batch search. Current Google Cloud docs describe BigQuery vector search with
managed vector indexes, `VECTOR_SEARCH`, and index types including IVF and
TreeAH. Google also documents that `VECTOR_SEARCH` and `CREATE VECTOR INDEX`
use BigQuery compute pricing, and that index storage size is visible through
`INFORMATION_SCHEMA.VECTOR_INDEXES`.

Use BigQuery for:

- scanning millions of trajectory fragments and cost traces;
- offline ranking and popularity/reuse analytics;
- vector-search experiments over cold fragments;
- cost attribution and billing analytics;
- model-route and cache-reuse event analysis;
- public or tenant-exported object snapshots.

Do not use BigQuery as the only operational store for review queues, login,
payments, tenant permissions, or hot object updates.

## Object Placement

| Data | First home | Later home |
| --- | --- | --- |
| Manifest YAML | Git + static docs | Git + static docs |
| Canonical generated objects | Postgres | Postgres plus BigQuery export |
| Embeddings for hot search | pgvector | pgvector plus BigQuery vector index |
| Raw source snapshots | Object storage | Object storage lifecycle tiers |
| JSONL/CSV load shards | Object storage or `dist/` during local runs | Object storage plus BigQuery external/import tables |
| Review tickets | Postgres | BigQuery export for analytics |
| Trace and cost events | Postgres initially | BigQuery as volume grows |
| Cache reuse events | Postgres hot path | BigQuery for aggregate savings analysis |

## Cost Rules

- Keep hot indexes small: only index promoted or frequently searched objects in
  Postgres.
- Batch-export cold rows from Postgres to object storage and BigQuery.
- Partition BigQuery tables by date/run/source surface and cluster by tenant,
  object type, domain, and fragment kind.
- Store raw blobs outside the database.
- Use BigQuery for batch analytics, not per-keystroke product search.
- Materialize small "serving slices" back into Postgres when product latency
  matters.
- Track estimated saved cost and latency for cache reuse events.

## Phases

1. Static site, Render API/worker, Postgres/pgvector, object storage.
2. Add queue workers for source scans, embeddings, labeling, and validation.
3. Export append-only tables to object storage and BigQuery.
4. Add BigQuery vector indexes for cold fragment search and analytics.
5. Promote useful serving slices back into Postgres or a dedicated low-latency
   vector service if needed.

## Sources

- BigQuery vector indexes: https://docs.cloud.google.com/bigquery/docs/vector-index
- BigQuery vector search overview: https://cloud.google.com/bigquery/docs/vector-search-intro
- BigQuery cost controls: https://docs.cloud.google.com/bigquery/docs/best-practices-costs
- Cloud SQL PostgreSQL AI/pgvector overview: https://docs.cloud.google.com/sql/docs/postgres/ai-overview
