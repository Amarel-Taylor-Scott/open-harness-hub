# Baltor Database-Backed Context Current State

Date: 2026-06-02

This file records the current state for the long-running database-backed
context migration goal.

## Current Direction

Baltor should not treat YAML and Markdown as the operational source of truth.
They remain valuable as:

```text
seed files
export files
review artifacts
static-site source
bootstrap snapshots
portable signed definitions
```

The hosted/runtime product should use database rows for:

```text
component definitions and versions
rubric dimensions and scores
context objects and versions
relationships and assertions
dimension definitions and values
artifacts and packs
lineage and feedback
mask and transformer contracts
business-object governance profiles
object contracts, schemas, layouts, diagrams, and context rules
settings/model/backend registries
```

## Recent Additions

Added durable goal prompt:

```text
.codex/prompts/baltor-database-backed-context-goal.md
```

Added archive policy:

```text
docs/archive/README.md
```

Added database-backed context docs:

```text
docs/codex/baltor-always-in-memory-context.md
archive/legacy/docs/architecture/database-backed-context-catalog.md
docs/architecture/baltor-business-object-governance-standard.md
archive/legacy/docs/architecture/baltor-architecture-context-providers.md
```

`docs/codex/baltor-always-in-memory-context.md` is the compact canonical
assistant context for Baltor. It defines Baltor as a verified context oracle,
states what Baltor is not, records the context-wizard worker taxonomy, and
anchors conflict, TTL, provider-boundary, security, and database-backed truth
rules for future work.

Added audit script:

```text
scripts/audit_context_storage.py
```

Added canonical Postgres tables:

```text
rubric_dimension
rubric_evaluation
rubric_dimension_score
component_context_object
context_mask_contract
context_transformer_contract
object_governance_profile
object_contract
object_schema_profile
object_layout_profile
object_architecture_diagram
object_context_rule
```

Added object-governance operational views:

```text
object_governance_profile_readiness
object_governance_family_coverage
object_governance_specialization_status
```

Admin operational readiness now includes an optional `database_probe` for those
views. Local runs continue to use schema/JSONL fallback data; hosted runs with
`DATABASE_URL` and a compatible Postgres driver can report live view presence
and row counts.

Release-scope validation now includes advisory object-governance drift checks
for both canonical table declarations and operational view declarations.

Added side-effect-free local Postgres smoke planner:

```text
scripts/db/object_governance_local_postgres_smoke_plan.py
```

It emits an operator-reviewed command plan that starts the local Postgres
container, initializes the canonical schema, loads object-governance seed rows,
checks seed coverage, and probes the operational views. It does not run Docker,
`psql`, or database mutations by itself.

Added object governance database seed package:

```text
db/seeds/object-governance/object_governance_profile.jsonl
db/seeds/object-governance/concrete_object_governance_profile.jsonl
db/seeds/object-governance/object_contract.jsonl
db/seeds/object-governance/concrete_object_contract.jsonl
db/seeds/object-governance/object_schema_profile.jsonl
db/seeds/object-governance/concrete_object_schema_profile.jsonl
db/seeds/object-governance/object_layout_profile.jsonl
db/seeds/object-governance/concrete_object_layout_profile.jsonl
db/seeds/object-governance/object_architecture_diagram.jsonl
db/seeds/object-governance/concrete_object_architecture_diagram.jsonl
db/seeds/object-governance/object_context_rule.jsonl
db/seeds/object-governance/concrete_object_context_rule.jsonl
db/seeds/object-governance/load-object-governance-seeds.sql
```

The family-level seed package currently covers:

```text
account_management
billing
context
flow
connection
process
database
identity
policy
integration
analytics
```

The first concrete object seed package currently covers profiles, contracts,
schema profiles, layouts, architecture diagrams, and context rules for:

```text
tenant
membership
billing_account
subscription
invoice
context_object
context_pack
source_connection
sync_job
pack_builder_process
principal
vector_index
```

Concrete object rows now include specialized contracts and schema rules for:

```text
tenant
membership
billing_account
subscription
invoice
context_object
context_pack
source_connection
sync_job
pack_builder_process
principal
vector_index
```

The consolidated registry-readiness status now reports both family seed
coverage and concrete object seed coverage so operators can see which runtime
object types still lack companion governance rows.

The catalog manifest bridge now treats rubric dimensions as database-backed
context objects, not only nested YAML fields. For rubric manifests it emits
`rubric_dimension` rows plus `context_object` rows with
`object_type = catalog_rubric_dimension`, source handles back to the seed
manifest and `db://rubric_dimension/...`, and
`component_context_object` bindings with role
`has_rubric_dimension_context`. This makes rubrics retrievable, auditable,
maskable, transformable, and packable at dimension granularity while keeping
the YAML manifest as a review/export artifact.

The manifest bridge and migration gate now also include explicit row-set and
reviewed-load plumbing for `context_mask_contract` and
`context_transformer_contract`. Processor manifests now emit conservative
`context_transformer_contract` rows using their declared `process_kind`,
`inputs`, `outputs`, determinism, idempotency, side-effect, implementation,
validation, and lineage fields. Manifests with direct redaction, PII, PHI, or
sensitive-data semantics now emit `context_mask_contract` rows with redaction
paths, policy triggers, entity-type hints, and source handles. The gate checks
duplicate contract IDs plus component/context-object references when rows
appear. The Postgres `component_context_object` role constraint now accepts
`has_rubric_dimension_context` so the generated rubric-dimension bindings are
loadable.

The `component_database_readiness` view now reports `mask_contract_count` and
`transformer_contract_count`. It flags loaded processor components as
`processor_transformer_contract_not_expanded` when no transformer contract rows
exist, making processor import drift visible from the database instead of only
from generated JSONL files.
The consolidated registry-readiness rollup now includes catalog operational
view readiness alongside object-governance operational view readiness, so
`--require-live-database` checks both view families when `DATABASE_URL` is set.
The admin demo operational-readiness payload now uses the same catalog
operational view registry and reports a catalog `database_probe` section under
`catalog_manifest_import`, so the UI/API visibility path matches the rollup.
The dry-run catalog database migration smoke now probes catalog operational
view declarations as a first-class step before Postgres load planning. The
latest smoke run passed with 27 steps and generated bridge rows for 2,664
components, 4,230 context objects, 1,566 rubric dimensions, 15 mask contracts,
and 175 transformer contracts. It also confirmed the load SQL references all
14 current row families, including `context_mask_contracts.jsonl` and
`context_transformer_contracts.jsonl`.
For catalog manifest bridge loads, the generated Postgres execution plan now
also includes a post-load `probe_catalog_operational_views` command using
`--require-database --require-views`, so operators verify live catalog views
before treating row-backed consumers as operationally ready.
The catalog database promotion-readiness gate now checks that the generated
load execution plan is ready and includes the post-load catalog operational
view probe. Current strict promotion readiness correctly fails only because the
database-exported smoke row snapshot is stale; advisory mode records
`database_export_snapshot_fresh` as the blocking check while confirming the
load execution plan and post-load probe plan are present.
The database-export smoke refresh plan now includes the same read-only
`probe_catalog_operational_views` command immediately after loading bridge rows
and before exporting refreshed database rows. This keeps the stale-snapshot
repair path aligned with the promotion gate: a refresh operator must prove live
catalog views are present and populated before treating the exported rows as
fresh.
The portable SQLite catalog snapshot now writes a
`catalog_snapshot_metadata` table with source kind, row directory, and
advisory `row_source_status`. This makes stale database-export snapshots
visible inside the generated SQLite cache, matching the browser index and
search-stats row-source metadata.
The row-backed catalog page generator now writes the same status into generated
`index.md` files, so human-facing catalog pages show when their backing
database-export rows are stale or not promotion-ready.
Vector index and vector-store artifacts now carry the same advisory status:
`build_vector_index.py` writes `row_source_status` into `_meta.json`, and
`build_vector_store.py` writes it into both the build report and
`vector_store_metadata`. This keeps vector caches from hiding stale
database-export rows.

Added adjacent market map:

```text
docs/strategy/baltor-adjacent-market-map.md
```

This strategy artifact records the market categories, closest watchlist,
provider/partner strategy, build-versus-integrate line, and positioning around
governed context packs. It is a review artifact, not operational truth; vendor
claims should be refreshed before external publication.
Added a market-map context bridge:

```text
scripts/db/market_map_context_bridge.py
dist/market-map-context-bridge/context_providers.jsonl
dist/market-map-context-bridge/context_objects.jsonl
dist/market-map-context-bridge/market-map-context-bridge-plan.json
```

The bridge emits 21 provider-contract rows and 33 context-object rows from the
adjacent market map without connecting to Postgres or mutating strategy docs.
This makes market categories, watchlist providers, and provider-strategy
relationships addressable as database-loadable context rather than prose-only
strategy notes.

Architecture modeling, service catalog, repo-wiki, event/API catalog, and
enterprise architecture tools are now documented as architecture context
providers. `schemas/context-provider.schema.json` accepts
`provider_type = architecture_context`, and
`archive/legacy/docs/architecture/baltor-architecture-context-providers.md` defines normalized
architecture object types, source handles, pack usage, drift checks, and first
provider priorities such as IcePanel, Structurizr, LikeC4, Backstage,
EventCatalog, and repo-wiki/code-context artifacts.

It also reports object-governance operational view readiness. Without
`DATABASE_URL`, the rollup checks canonical schema declarations. With
`DATABASE_URL` or `--database-url`, it includes live database view presence and
row-count readiness through the same read-only probe used by the admin surface.
The rollup remains advisory by default, but `--require-ready` and
`--require-live-database` turn it into a non-zero-exit validation gate for CI or
operator smoke checks.
Archive/rot checks can also be gated without moving files by using
`--max-rotted-severity` for raw audit findings or
`--max-archive-registry-severity` for the database seed/export registry.
Archive candidate registry integrity is tracked separately from severity:
`--require-archive-registry-integrity` fails only when generated
`context_archive_candidate` seed/export rows have duplicate registry keys or
missing source hashes.

## Active Parallel Agents

Three parallel agents were started for disjoint scopes:

```text
database migration/import-export
rotted-context audit and archive policy
hard-coded settings and registry/config cleanup
```

## Important Constraints

Do not:

```text
delete or move files without approval
terminate unrelated processes
silently rename published component IDs
make the database the only path for static public docs
store secrets/PII/customer data in examples
add more hard-coded lists
```

## Next Backlog

Highest-value next steps:

```text
1. Build a manifest-to-database import/export skeleton.
2. Expand rubric dimensions into rubric_dimension rows during import.
3. Add broader mask extraction for projection, permission, local-sync, export,
   and summary-view masks once manifests declare those contracts explicitly.
4. Add a settings/model/backend registry and remove repeated model/vector literals.
5. Add deeper companion variants for high-risk concrete objects, such as
   separate API, event, database, UI, policy, and analytics contracts where a
   single baseline contract is not specific enough.
6. Tune scripts/audit_context_storage.py for fast routine operation.
7. Generate a rotted-context candidate ledger without moving files.
8. Add validation checks for database-backed registry drift.
9. Add SQL views for operational dashboards.
```

## Validation So Far

Known passing checks:

```text
python3 -m py_compile scripts/audit_context_storage.py
python3 -m py_compile scripts/validate.py scripts/db/registry_readiness_status.py
python3 -m py_compile scripts/build_catalog_db.py scripts/db/catalog_database_migration_smoke.py
python3 -m py_compile scripts/db/build_vector_index.py scripts/db/build_vector_store.py
python3 -m py_compile scripts/db/market_map_context_bridge.py
python3 -m py_compile scripts/db/catalog_manifest_bridge.py scripts/db/catalog_manifest_migration_gate.py
python3 scripts/validate.py catalog/rubrics/baltor-business-object-governance-quality.yaml
python3 scripts/validate.py catalog/processors/connectors/mcp-confluence-connector.yaml catalog/processors/connectors/mcp-gitlab-connector.yaml catalog/processors/connectors/mcp-postgres-connector.yaml
python3 scripts/db/catalog_manifest_bridge.py --self-test
python3 scripts/db/catalog_manifest_migration_gate.py --self-test
python3 scripts/db/market_map_context_bridge.py --self-test
python3 scripts/db/market_map_context_bridge.py --output-dir dist/market-map-context-bridge
python3 scripts/db/catalog_operational_view_probe.py --self-test
python3 scripts/db/catalog_database_migration_smoke.py --output dist/catalog-migration-smoke/catalog-database-migration-smoke.json
python3 scripts/db/catalog_database_promotion_readiness.py --self-test
python3 scripts/db/catalog_database_promotion_readiness.py --advisory --output dist/catalog-migration-smoke/catalog-database-promotion-readiness.json
python3 scripts/db/catalog_db_export_smoke_refresh_plan.py --self-test
python3 scripts/db/catalog_db_export_smoke_refresh_plan.py --bridge-dir dist/catalog-manifest-bridge --db-row-dir dist/catalog-db-export-rows-smoke --output dist/catalog-migration-smoke/catalog-db-export-smoke-refresh-plan.json
python3 scripts/build_catalog_pages.py --row-dir dist/catalog-db-export-rows-smoke --output-dir /tmp/catalog-pages-status-smoke
python3 scripts/build_catalog_db.py --row-dir dist/catalog-db-export-rows-smoke --output /tmp/catalog-from-db-metadata-smoke.sqlite
python3 scripts/db/build_vector_index.py --row-dir dist/catalog-db-export-rows-smoke --embedder hash --output-dir /tmp/vector-index-status-smoke
python3 -m scripts.db.build_vector_store --row-dir dist/catalog-db-export-rows-smoke build --store /tmp/vector-store-status-smoke.sqlite --model hash-bow-v1 --limit 25
python3 scripts/db/object_governance_registry.py --check-seed-coverage
python3 scripts/db/registry_readiness_status.py --format markdown
python3 scripts/db/registry_readiness_status.py --format json
python3 scripts/db/registry_readiness_status.py --require-ready
python3 scripts/db/registry_readiness_status.py --max-rotted-severity 5
python3 scripts/db/registry_readiness_status.py --max-archive-registry-severity 5
python3 scripts/db/registry_readiness_status.py --require-archive-registry-integrity
python3 scripts/db/registry_readiness_status.py --database-url "$DATABASE_URL" --require-ready --require-live-database
python3 scripts/db/object_governance_local_postgres_smoke_plan.py --self-test
python3 scripts/db/object_governance_view_probe.py --self-test
python3 -c "import scripts.baltor_admin_demo_server as s; print(s.operational_readiness_payload()['object_governance']['views'])"
python3 -c "import scripts.baltor_admin_demo_server as s; print(s.operational_readiness_payload()['object_governance']['database_probe'])"
```
