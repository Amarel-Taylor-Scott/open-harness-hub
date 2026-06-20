# Generated Object Storage

JSONL is the interchange and staging format for object factories. It is not the canonical operational store for a million generated components and subcomponents.

The canonical hosted shape is:

```text
factory JSONL shard
-> validation and privacy gates
-> Postgres canonical tables
-> pgvector/object_embedding rows
-> index_record rows
-> partition_manifest and index_delta rows
-> replayable search/vector/quality/facet/cost indexes
```

## Storage Roles

| Layer | Role |
|---|---|
| JSONL | Portable batch interchange, local tests, static docs examples, object-store shards |
| Postgres | Canonical components, subcomponents, source records, normalized objects, entities, labels, dimensions, promotion decisions, review queues |
| pgvector | Default vector store colocated with canonical rows |
| Object storage | Raw snapshots, large JSONL shards, generated media, components |
| Search/index rows | Keyword, facet, quality, freshness, graph, and cost records derived from canonical data |

## Why Keep JSONL At All?

JSONL is cheap, append-friendly, easy to validate in CI, and easy for workers to stream. It is the right format for seed packs and partition files. Production should load those rows into Postgres, then treat the database as the authority.

## Canonical Tables

The schema in `db/postgres/schema.sql` includes:

- `source_record`
- `normalized_object`
- `canonical_entity`
- `object_entity_ref`
- `dedupe_cluster`
- `review_ticket`
- `promotion_decision`
- `index_record`
- `partition_manifest`
- `index_delta`
- `object_embedding`

`object_embedding` uses pgvector by default. The baseline dimension is 384 for local MiniLM-style embeddings; deployments using larger embeddings can add a parallel table or migrate the vector dimension.

## Loader Path

For local and CI use:

```bash
python3 -m scripts.db.factory_jsonl_to_postgres \
  --source-records catalog/knowledge-packs/data/task-marketplace-archetype-patterns/source-records.jsonl \
  --normalized-objects catalog/knowledge-packs/data/task-marketplace-archetype-patterns/archetype-patterns.jsonl \
  --promotion-decisions catalog/knowledge-packs/data/promotion-index-delta-patterns/promotion-decisions.jsonl \
  --output dist/sql/factory-load.sql
```

Apply with `psql` in an environment that has run `db/postgres/schema.sql`.

Generated SQL is intentionally reviewable. Later hosted workers can replace this with direct batched inserts, COPY, or queue consumers.

## Count Reporting

Do not use the repository file count as the generated component count. The catalog count measures reviewed seed/export definitions; high-volume generated components and subcomponents are counted in Postgres and staged JSONL shards.

Use `scripts/db/object_count_report.py` for local staged JSONL counts and `db/postgres/object_count_report.sql` for canonical database row counts. See `docs/architecture/object-counts-and-db-bootstrap.md` for the bootstrap and reporting workflow.
