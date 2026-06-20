# Local Postgres + pgvector

This compose file is for local development and ingestion tests. It is not a production secrets template.

Start the database:

```bash
docker compose -f infra/postgres/docker-compose.pgvector.yml up -d
```

Set the local connection string:

```bash
export DATABASE_URL="postgresql://open_harness:open_harness_dev@localhost:5432/open_harness_hub"
```

Initialize the schema:

```bash
psql "$DATABASE_URL" -f db/postgres/schema.sql
```

Generate loader SQL from staged JSONL:

```bash
python3 -m scripts.db.factory_jsonl_to_postgres \
  --source-records catalog/knowledge-packs/data/task-marketplace-archetype-patterns/source-records.jsonl \
  --normalized-objects catalog/knowledge-packs/data/task-marketplace-archetype-patterns/archetype-patterns.jsonl \
  --promotion-decisions catalog/knowledge-packs/data/promotion-index-delta-patterns/promotion-decisions.jsonl \
  --output dist/sql/factory-load.sql
```

Apply the load and count rows:

```bash
psql "$DATABASE_URL" -f dist/sql/factory-load.sql
psql "$DATABASE_URL" -f db/postgres/object_count_report.sql
```

For Render, Supabase, Neon, Railway, or other managed Postgres, use the same schema/load/count sequence against the managed `DATABASE_URL`.
