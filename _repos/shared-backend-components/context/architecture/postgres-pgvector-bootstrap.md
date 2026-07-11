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

See the consolidated **Bulk load path** section below.

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

## Load, count, and audit stages (consolidated)

> Folds the durable design of the merged Postgres/load plans — object-counts-and-db-bootstrap, the bulk generated-object load path, the candidate-store and template load plans, the load execution plan, and the staged-vs-committed / daily-partition audits. Frozen per-run sample counts live in the archived source docs; the contracts below are the durable part. Every planner here is side-effect free (writes CSV/SQL/JSON only) — actual database execution stays a separate operator/worker step that supplies committed counts.

### Object counts — three levels, never collapsed

The product reports **three distinct counts**, never one flat number:

- **curated repository-definition count** — reviewed seed/export definitions in `catalog/`;
- **staged generated-row count** — operational rows in factory JSONL / bulk-CSV shards (source records, normalized objects, labels, dimensions, entity links, dedupe clusters, embeddings, review tickets, promotion decisions, index deltas);
- **committed canonical count** — rows actually in Postgres, proven by `db/postgres/object_count_report.sql`.

A flat "N objects" claim is misleading unless it says which level it means. Do NOT inflate repository files to reach a million rows — keep file definitions curated and compact; put high-volume candidates in Postgres + object storage and promote only reviewed items. For million-object runs every count report separates: component-definition, source-record, normalized-object, embedding, index-record/delta, review-ticket, promotion-decision, and label/dimension counts. Local staging counts come from `scripts/db/object_count_report`; canonical counts from the SQL report.

### Bulk load path (for batches too large for reviewable per-row SQL)

```text
factory JSONL shards -> CSV export by canonical table -> psql \copy into temp staging tables -> upsert into canonical Postgres tables -> object_count_report.sql
```

`scripts/db/factory_jsonl_bulk_copy` exports CSV + `load.sql` for the canonical tables: `source_record`, `normalized_object`, `dedupe_cluster`, `canonical_entity`, `object_entity_ref`, `promotion_decision`, `review_ticket`, `label_assignment`, `dimension_value`, `object_embedding`, `index_record`. Run `scripts/db/factory_jsonl_relationship_preflight.py` before export to catch missing local references while the batch is still cheap to repair. Safety: validate and privacy-screen JSONL before export; keep raw snapshots and very large shards in object storage; Postgres is the canonical state after load; keep manifest counts separate from database-row counts.

### Candidate store load (generated rows never jump straight to active)

`scripts/db/component_store_load_plan` targets the candidate tables that sit between staged factory output and active `component`/`subcomponent` rows: `component_candidate`, `subcomponent_candidate`, `source_component_link`. Candidate tables let ingestion scale without overstating quality — generated rows are counted honestly, source/license/trust/privacy metadata stays attached, high-risk rows stay review-gated, promotion happens later without re-running ingestion, and rejected/held rows stay useful for dedupe and audits. Load order: source records + normalized objects → component candidates → subcomponent candidates → source-component links → committed-count audit → promote reviewed candidates.

### Template load (pipeline templates become rows, not loose JSON)

`scripts/db/component_template_load_plan` turns generated template JSON into `component_pipeline_template` + `component_pipeline_template_step` rows (loaded in that order). Each step keeps step order, component layer, optional control-flow kind, resolved active-component id and/or candidate id when available, and the original reference in `body.component_ref` — preserving unresolved references matters at scale because useful templates are generated before every referenced component is promoted. Templates are product-facing, so they get their own review gate (generation → load planning → staged load → staged-vs-committed audit → layer-coverage audit → cost-route audit → publication) and each template and step is embedded as a separate search subject so a user can retrieve a whole off-the-shelf pipeline or a modular piece (a cheaper `llm` route, a stricter `post_llm` verifier, a safer `control_flow.human_review` branch).

### Load execution plan (applies SQL, exports committed counts)

The execution planner emits ordered operator commands: start local pgvector (Docker target) → set `DATABASE_URL` → init `schema.sql` → apply `load.sql` → probe catalog operational views for catalog-manifest bridge loads → run `object_count_report.sql` → convert `psql --csv` to JSON → run the staged-vs-committed audit. It targets local Docker, Render, or managed Postgres with pgvector, contains no credentials, and never runs Docker or mutates a database itself. For catalog-manifest bridge loads, committed counts alone are not enough — the read-only `catalog_operational_view_probe.py` also verifies the dashboard views exist and have rows before consumers treat the load as operationally ready.

### Staged-vs-committed audit (what is actually proven)

Generated JSONL counts are not canonical database counts. The audit reads a load-plan manifest (staged bulk counts + `load.sql`), optional machine-readable rows from `object_count_report.sql`, and optional execution metadata, then returns one status: **`verified`** (committed counts supplied and every audited relation matches staged), **`staged_only`** (staged + preflight-clean but no committed counts), or **`mismatch`** (a committed relation count differs from staged). It checks the canonical high-volume relations (source records, normalized objects, canonical entities, object/entity refs, dedupe clusters, review tickets, promotion decisions, index records, object embeddings, label assignments, dimension values). Operating rule: public dashboards use committed counts when available and label staged counts as staged; million-object claims require committed counts or a clearly stated storage tier (object storage + verified load manifests).

### Daily partition load audit (dedupe before bulk export)

Additive daily generation repeatedly hits shared source records, canonical entities, and labels, so a raw line count overstates the rows that will exist after Postgres upsert. The partition audit (`scripts/db/daily_partition_load_audit`) reads one or more daily partition directories, merges each row family by its canonical primary key, runs local relationship preflight, and emits merged JSONL, a preflight report, CSV for `\copy`, `bulk-copy/load.sql`, a load-plan manifest, a staged-vs-committed audit, and a summary. Merging by primary key before bulk export keeps expected Postgres counts honest and stops dashboards mistaking raw generated lines for committed reusable components. Output stays `staged_only` until an operator applies the SQL and supplies committed counts.
