# Postgres pgvector Bootstrap

Generated primitives need a canonical database before the hub can honestly claim hundred-thousand or million-object scale. YAML manifests remain curated definitions; Postgres owns high-volume object state.

## Local Bootstrap

Start local pgvector:

```bash
docker compose -f infra/postgres/docker-compose.pgvector.yml up -d
```

Set the database URL:

```bash
export DATABASE_URL="postgresql://open_harness:open_harness_dev@localhost:5432/open_harness_hub"
```

Initialize schema, emit loader SQL, apply it, and count rows:

```bash
psql "$DATABASE_URL" -f db/postgres/schema.sql
python3 -m scripts.db.factory_jsonl_to_postgres \
  --source-records catalog/knowledge-packs/data/task-marketplace-archetype-patterns/source-records.jsonl \
  --normalized-objects catalog/knowledge-packs/data/task-marketplace-archetype-patterns/archetype-patterns.jsonl \
  --promotion-decisions catalog/knowledge-packs/data/promotion-index-delta-patterns/promotion-decisions.jsonl \
  --output dist/sql/factory-load.sql
psql "$DATABASE_URL" -f dist/sql/factory-load.sql
psql "$DATABASE_URL" -f db/postgres/object_count_report.sql
```

Or emit a machine-readable plan:

```bash
python3 -m scripts.db.postgres_bootstrap_plan --output dist/reports/postgres-bootstrap-plan.json
```

For larger batches, use the bulk CSV staging path instead of per-row SQL:

```bash
python3 -m scripts.db.factory_jsonl_bulk_copy \
  --source-records catalog/knowledge-packs/data/task-marketplace-archetype-patterns/source-records.jsonl \
  --normalized-objects catalog/knowledge-packs/data/task-marketplace-archetype-patterns/archetype-patterns.jsonl \
  --promotion-decisions catalog/knowledge-packs/data/promotion-index-delta-patterns/promotion-decisions.jsonl \
  --output-dir dist/bulk/factory-load
psql "$DATABASE_URL" -f dist/bulk/factory-load/load.sql
```

See `docs/architecture/bulk-generated-object-loads.md`.

## Render or Managed Postgres

Use the same schema/load/count sequence against a managed `DATABASE_URL`. The managed database must support `CREATE EXTENSION vector`.

For Render, the initial product shape is:

- static docs on GitHub Pages or Cloudflare Pages;
- API service on Render;
- background worker on Render;
- Render Postgres or another managed Postgres with pgvector;
- Redis/queue for ingest, polish, embedding, and pricing refresh jobs;
- object storage for raw snapshots and large JSONL shards.

## Readiness Gate

A database-backed factory run is not ready until it has:

- initialized schema successfully;
- loaded source records and normalized objects;
- emitted review tickets or documented why no review is required;
- emitted index records or index deltas;
- run `db/postgres/object_count_report.sql`;
- published separate manifest, staged JSONL, and canonical database row counts.

For local work without a running database, staged JSONL counts are useful, but they are not canonical object counts.
