# Incremental Catalog Builds

Full validation and full page rebuilds are acceptable as release checks, but they do not scale to one million or ten million components. The default factory path should be additive: validate changed public definitions, render changed pages, append index deltas, and update search/vector stores by partition.

Full rebuilds should become release, migration, and disaster-recovery operations.

## Hard Rule

Do not block daily 1,000 to 5,000 component candidate generation on a full static docs rebuild. The daily path is database-first:

1. generate JSONL row families;
2. load-audit the partition;
3. emit SQL and index deltas;
4. plan review and promotion;
5. plan or run embeddings;
6. audit vector and committed-load readiness.

Static docs should document the factories, sampled components, and runbooks. They are not the storage mechanism for millions of components.

## Build Modes

| Mode | Use when | Work performed |
|---|---|---|
| Changed-manifest validation | Normal Codex or factory batch | Validate only edited manifests against schemas and vocabularies; skip global reference checks unless requested |
| Selected page render | Normal docs update | Render only pages for changed manifests |
| Partition index update | Large catalog batches | Append or replace one partition index such as `type=tool/date=2026-05-25` |
| Search delta update | SaaS ingestion | Upsert keyword, vector, graph, facet, quality, cost, and freshness records for changed object ids |
| Full rebuild | Release snapshot, schema migration, corruption recovery | Recompute every page, index, vector, graph, and aggregate |

## Local Commands

Validate specific manifests:

```bash
python3 scripts/validate.py catalog/tools/page-to-markdown-converter.yaml catalog/pipelines/research-web/object-factory-worker-fleet.yaml
```

Selected-path validation skips the expensive global cross-component reference scan by default. Use it for leaf tools, docs-backed manifests, or isolated additions. For selected validation with full reference verification, run:

```bash
python3 scripts/validate.py --global-ref-check catalog/pipelines/research-web/object-factory-worker-fleet.yaml
```

Build or check the component-id cache used by selected global ref checks:

```bash
python3 scripts/build_component_id_index.py --update catalog/tools/page-to-markdown-converter.yaml catalog/pipelines/research-web/object-factory-worker-fleet.yaml
python3 scripts/build_component_id_index.py --check-fresh
```

Use the full cache rebuild only for release snapshots, broad path changes, cache corruption, or duplicate-id investigation:

```bash
python3 scripts/build_component_id_index.py
```

When the cache is fresh, `--global-ref-check` loads `dist/catalog-component-ids.json` instead of parsing every manifest. If the cache is stale or missing, validation falls back to a full catalog scan.

Render specific catalog pages and merge their links into the existing catalog index without scanning the whole catalog:

```bash
python3 scripts/build_catalog_pages.py --paths catalog/tools/page-to-markdown-converter.yaml --update-index
```

Use page-only rendering when the entries are already indexed or a draft should not change the central index:

```bash
python3 scripts/build_catalog_pages.py --paths catalog/tools/page-to-markdown-converter.yaml --skip-index
```

Run a full rebuild only when required:

```bash
python3 scripts/validate.py
python3 scripts/build_catalog_pages.py
```

## Million-Object Rule

At one million objects, do not model every object as a standalone Markdown page. Use:

- manifests for curated reusable primitives, pipelines, tools, rubrics, datasets, and packs;
- JSONL shards for high-volume source-derived objects;
- partition manifests for batches;
- database/search indexes for interactive discovery;
- generated docs pages only for curated components, partition summaries, and sampled examples.

For the local runnable path, `scripts/factory/index_delta_emitter.py` turns a normalized-object JSONL shard into:

- `partition-manifest.json`;
- `index-deltas.jsonl`;
- idempotent keyword/facet/freshness/quality upsert records.

Run:

```bash
python3 -m scripts.factory.index_delta_emitter --self-test
```

## Ten-Million-Object Rule

At ten million objects, every ingestion run should produce append-only deltas:

- `source_record` deltas;
- normalized object JSONL shards;
- label and dimension shards;
- embedding batches;
- graph edge batches;
- dedupe cluster updates;
- review-ticket batches;
- search-index upserts.

The SaaS backend should treat static docs as a public product surface, not the primary database.

## Operational Invariants

- Every delta must carry a run id, source snapshot id, schema version, and content hash.
- Every index record must be reproducible from a source record, curated manifest, or signed publisher submission.
- A failed partition update must be replayable without rewriting unrelated partitions.
- Full rebuilds must be deterministic enough to compare aggregate counts, hashes, and partition manifests.
- Review queues must be partition-aware so unsafe or low-confidence batches can be quarantined without blocking unrelated ingestion.
- Fast validation caches must be treated as derived components. They can accelerate checks, but full validation remains the authority for release snapshots and schema migrations.
