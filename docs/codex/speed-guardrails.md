# Speed Guardrails

The million-component goal cannot rely on full static-site rebuilds after every factory turn. Static docs are a public product surface. The database, JSONL partitions, load plans, and search indexes are the scaling surface.

## Default Loop

For normal component factory work:

1. generate database-backed JSONL row families;
2. run staged load audit and relationship preflight;
3. emit SQL or copy plans without applying them;
4. run promotion, review, embedding, vector-readiness, and committed-load planners;
5. validate only changed public component definitions;
6. render only changed catalog pages with `--update-index` for new public definitions, or `--skip-index` for page-only edits that do not need index changes.

Use full validation and full page rebuilds for release snapshots, schema or vocabulary changes, broad reference rewires, corruption recovery, or explicit user requests.

## Fast Commands

Focused validation:

```bash
python3 scripts/validate.py catalog/tools/example.yaml catalog/pipelines/research-web/example.yaml
```

Focused validation with global refs using the cache:

```bash
python3 scripts/build_component_id_index.py --update catalog/tools/example.yaml catalog/pipelines/research-web/example.yaml
python3 scripts/validate.py --global-ref-check catalog/pipelines/research-web/example.yaml
```

Use `--check-fresh` when you need to verify the cache without changing it:

```bash
python3 scripts/build_component_id_index.py --check-fresh
```

Selected docs render:

```bash
python3 scripts/build_catalog_pages.py --paths catalog/tools/example.yaml catalog/pipelines/research-web/example.yaml --update-index
```

Use `--skip-index` only when the changed definitions are already indexed or when you are intentionally avoiding any index mutation:

```bash
python3 scripts/build_catalog_pages.py --paths catalog/tools/example.yaml --skip-index
```

Full release gate:

```bash
python3 scripts/validate.py
python3 scripts/build_component_id_index.py
python3 scripts/build_catalog_pages.py
```

## Regression Rules

- Do not block daily 1K to 5K candidate generation on a full docs rebuild.
- Do not report public YAML count as the main scaling metric.
- Do not treat generated JSONL rows as committed database rows.
- Do not treat pgvector load SQL as product-ready vector search.
- Do not promote high-risk rows without review evidence.
- Do not store real PII, secrets, proprietary dumps, or unlicensed source text to hit volume targets.
- Do not add full rebuild steps to every factory script.

## Required Metrics

Every daily or theory batch closeout should report:

- public component definition count;
- generated normalized component candidates;
- unique staged rows;
- candidate load SQL path;
- review-ticket count;
- embedding planned rows;
- vector-ready rows;
- pgvector load-accepted and rejected rows;
- committed Postgres counts, if actually exported;
- audit status.

## North Star

The fast path is additive and replayable: append new source partitions, compute deltas, upsert database/search rows, and keep docs focused on curated components, sampled examples, and operator runbooks.
