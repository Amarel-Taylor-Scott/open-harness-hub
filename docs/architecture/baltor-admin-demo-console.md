# Baltor Admin Demo Console

The admin demo root is intentionally a card-only console:

1. Load data
2. Processing
3. Outputs
4. Download
5. Explore context
6. Integration testing

The root page should stay quiet. It acts as a launcher and status summary, not a
dense dashboard. Each operational surface gets a dedicated route:

- `/admin-demo/sources`
- `/admin-demo/monitoring`
- `/admin-demo/outputs`
- `/admin-demo/download`
- `/admin-demo/explore`
- `/admin-demo/testing`

The root route should show only these launcher cards. Navigation chrome,
processing details, graph browsing, RAG chat, export controls, and integration
checks belong on the dedicated pages.

## Front-End Structure

The static frontend is split into small modules under
`web/openhubforai/admin-demo-assets/`:

- `app.js`: route and event orchestration
- `api.js`: HTTP calls to the demo run API
- `dom.js`: DOM helpers and escaping
- `renderers.js`: UI rendering functions
- `sample.js`: synthetic demo context

`web/openhubforai/admin-demo.js` is only a module loader. This keeps the page
easy to evolve without rebuilding the whole frontend stack.

## Export Endpoints

Completed demo runs expose real downloadable packages:

```text
GET /api/admin-demo/runs/{run_id}/exports/text
GET /api/admin-demo/runs/{run_id}/exports/rag
GET /api/admin-demo/runs/{run_id}/exports/graph
GET /api/admin-demo/runs/{run_id}/exports/audit
```

Package shapes:

- `text`: JSON text pack with candidate facts, state, confidence, source chunk,
  signals, and provenance history including the original customer-source fact.
- `rag`: JSONL records for chunks with claim metadata, source metadata, and
  freshness labels.
- `graph`: GraphML containing entity, chunk, and claim nodes plus support and
  mention edges.
- `audit`: ZIP packet with manifest, sources, worker plan, claims, verification
  queue, and automated refresh jobs.

The Download card should remain quiet until a run is complete. After a completed
run has extracted claims, the export buttons become active and download the
run-specific packages.

## Provenance Display

The Outputs view should show lightweight lineage before users download anything:

- verification queue rows show the source chunk and that the original
  customer-source claim is retained in export provenance;
- extracted claim rows show source chunk, confidence, and provenance tags;
- source sync rows show version, content hash, last sync label, change state,
  and next action.

The Explore view should reuse the same run payload rather than inventing a
separate demo state:

- graph stats come from extracted nodes and chunks;
- the data browser shows candidate facts with state, confidence, source chunk,
  and signals;
- the RAG chat preview answers from the generated package shape and makes clear
  that live model answering is outside the static demo.

The Integration Testing view should also be run-aware. It should summarize
connector sync, worker follow-up jobs, export contracts, model route decisions,
and governance gates from the current run so it behaves like a readiness console
instead of a static checklist.

It also exposes database-backed operating-readiness signals. The demo does not
need a live Postgres connection to show these contracts; it should make the
transition visible by reading generated seed/import artifacts and canonical
schema capabilities:

- catalog manifest import status from the bridge output;
- generated context-object and rubric-dimension row counts;
- object governance package status for contracts, schemas, layouts, diagrams,
  and context rules;
- archive-candidate review contract and non-destructive audit command;
- setting registry and drift-audit status for model routes, vector backends,
  embedding dimensions, thresholds, and cloud settings.

Current endpoint:

```text
GET /api/admin-dashboard/operational-readiness
```

The same payload is also rendered on the live monitor page:

```text
GET /admin-dashboard/monitor
```

MCP wrapper tool:

```text
context_operational_readiness
```

The endpoint is a visibility contract. Hosted deployments should eventually
source these fields from database views such as
`catalog_manifest_import_status`, `component_database_readiness`, and
`rubric_dimension_tree`; the local demo may fall back to generated JSONL and
schema inspection.

Catalog bridge readiness now also reports a `database_probe` section using the
same expected view registry as the consolidated readiness rollup. With
`DATABASE_URL`, hosted runs can confirm catalog view presence and row counts;
without it, the demo still verifies the canonical schema declarations.

For object-governance readiness, the endpoint now keeps the local fallback and
also reports a `database_probe` section. If `DATABASE_URL` is configured and a
compatible Postgres driver is available, the probe checks the object-governance
views and returns their row counts; otherwise it reports why database probing
was skipped.

## Product Language

Use calm operational labels:

- `Verification queue`, not `fragile facts`
- `Automated refresh jobs`, not `worker refresh queue`
- `Processing pipeline`, not `K8 worker process`
- `Knowledge graph`, not `context graph`
- `Serving packages`, not `consumable context`

Manual confirmation should be rare and should be shown as an exception state
after deterministic, scoped model, and Hermes/OpenClaw workers fail to resolve
the case.
