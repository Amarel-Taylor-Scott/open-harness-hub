# Object Counts and Database Bootstrap

The repository definition count and the generated component count are different product metrics.

`component_definition_count` is the number of curated repository definitions in `catalog/`. These are reviewed seed/export definitions for tools, pipelines, harnesses, knowledge packs, rubrics, adapters, and related component types.

`generated_component_count` is the number of operational component and subcomponent rows in the database-backed factory store: source records, normalized procedure objects, labels, dimensions, entity links, dedupe clusters, embeddings, review tickets, promotion decisions, and index deltas.

## Target Shape

```text
catalog/*.yaml                    -> seed/export component definitions
factory JSONL shards              -> portable staging and object storage
Postgres tables                   -> canonical component and subcomponent state
pgvector object_embedding rows    -> local vector retrieval baseline
index_record + index_delta rows   -> replayable keyword/vector/graph/facet indexes
object_count_report               -> separate repository-definition and database-row metrics
```

The product should report both counts. A flat statement like "4,095 objects" is misleading unless it explicitly says "4,095 curated component definitions."

## Bootstrap Stages

1. Run `db/postgres/schema.sql` in a Postgres instance with pgvector installed.
2. Emit loader SQL from staged factory JSONL shards.
3. Apply the loader SQL with `psql`.
4. Run `db/postgres/object_count_report.sql`.
5. Publish a count report that separates curated component definitions from generated database rows.

Local staging count example:

```bash
python3 -m scripts.db.object_count_report \
  --jsonl source_record=catalog/knowledge-packs/data/task-marketplace-archetype-patterns/source-records.jsonl \
  --jsonl normalized_object=catalog/knowledge-packs/data/task-marketplace-archetype-patterns/archetype-patterns.jsonl \
  --jsonl promotion_decision=catalog/knowledge-packs/data/promotion-index-delta-patterns/promotion-decisions.jsonl \
  --output dist/reports/object-count-report.json
```

Canonical database count example:

```bash
psql "$DATABASE_URL" -f db/postgres/object_count_report.sql
```

For local pgvector setup, Render, or other managed Postgres targets, see `_repos/shared-backend-components/context/architecture/postgres-pgvector-bootstrap.md`.

## Scale Policy

Do not inflate repository files to reach one million rows. Keep file-based definitions curated and compact. Put high-volume generated candidates in Postgres and object storage, then promote only the most useful, stable, and reviewed items into public components.

For million-object runs, every count report should include:

- component definition count;
- source record count;
- normalized object count;
- embedding count;
- index record and index delta count;
- review ticket count;
- promotion decision count;
- label and dimension assignment count.
