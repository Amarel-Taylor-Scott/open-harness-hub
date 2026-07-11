# Bulk Generated Object Loads

The row-by-row SQL loader is useful for small seed batches and human review. Million-object runs need a bulk path.

The bulk path is:

```text
factory JSONL shards
-> CSV export by canonical table
-> psql \copy into temporary staging tables
-> upsert into canonical Postgres tables
-> object_count_report.sql
```

Use it when a batch is too large for reviewable per-row SQL.

## Local Command

```bash
python3 -m scripts.db.factory_jsonl_bulk_copy \
  --source-records catalog/knowledge-packs/data/task-marketplace-archetype-patterns/source-records.jsonl \
  --normalized-objects catalog/knowledge-packs/data/task-marketplace-archetype-patterns/archetype-patterns.jsonl \
  --promotion-decisions catalog/knowledge-packs/data/promotion-index-delta-patterns/promotion-decisions.jsonl \
  --output-dir dist/bulk/factory-load
```

Apply after `db/postgres/schema.sql` has run:

```bash
psql "$DATABASE_URL" -f dist/bulk/factory-load/load.sql
psql "$DATABASE_URL" -f db/postgres/object_count_report.sql
```

## Supported Tables

The initial bulk exporter supports:

- `source_record`
- `normalized_object`
- `dedupe_cluster`
- `canonical_entity`
- `object_entity_ref`
- `promotion_decision`
- `review_ticket`
- `label_assignment`
- `dimension_value`
- `object_embedding`
- `index_record`

These tables cover source provenance, generated objects, fuzzy dedupe, entity linking, promotion scoring, human review routing, hierarchical labels, flexible dimensions, embeddings, and search/index records. Use `scripts/db/factory_jsonl_relationship_preflight.py` before bulk export to catch missing local references while a batch is still cheap to repair.

## Safety Rules

- Validate and privacy-screen JSONL before bulk export.
- Keep raw snapshots and very large shards in object storage.
- Use Postgres as the canonical object state after load.
- Count loaded rows with `db/postgres/object_count_report.sql`.
- Keep YAML manifest counts separate from canonical database row counts.
