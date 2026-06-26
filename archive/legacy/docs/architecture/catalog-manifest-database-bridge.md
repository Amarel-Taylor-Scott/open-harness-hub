# Catalog Manifest Database Bridge

Catalog manifests should not be operational truth in the hosted product.

They should be:

```text
reviewable seeds
portable exports
static-site source
disaster-recovery snapshots
signed publication bundles
```

The operational database should own:

```text
current component state
component versions
rubric dimensions
component relationships
context-object bindings
import history
rotted-context flags
evaluation results
runtime feedback
lineage
analytics
```

This bridge standard defines how YAML manifests become database rows without
moving or deleting the existing catalog files.

## Import Flow

```text
catalog/*.yaml
  -> schema validation
  -> manifest hash
  -> manifest_import_batch
  -> manifest_import_record
  -> component
  -> component_version
  -> component_industry / capability / modality / tag
  -> component_ref
  -> rubric_dimension, for rubrics
  -> context_object
  -> component_context_object
  -> context_mask_contract, for redaction/sensitive-data masks
  -> context_transformer_contract, for processors
```

The current bridge script is:

```bash
python3 scripts/db/catalog_manifest_bridge.py
```

It writes JSONL row sets and a reviewable psql load script under:

```text
dist/catalog-manifest-bridge/
```

The script does not connect to Postgres. It is a planner and export generator.

Before applying the generated SQL, run the migration gate:

```bash
python3 scripts/db/catalog_manifest_migration_gate.py \
  --row-dir dist/catalog-manifest-bridge \
  --output dist/catalog-manifest-bridge/migration-gate-report.json
```

The gate is fail-closed. It blocks the load when duplicate, review, or archive
recommendations have not been explicitly allowed. After curator review, pass
the accepted counts:

```bash
python3 scripts/db/catalog_manifest_migration_gate.py \
  --row-dir dist/catalog-manifest-bridge \
  --output dist/catalog-manifest-bridge/migration-gate-report.json \
  --allow-hold-count 4 \
  --allow-review-count 743
```

The allowed counts are not permanent settings. They are per-batch approval
evidence that the current held duplicates and review candidates were seen
before loading.

After the gate passes, emit a side-effect-free Postgres execution plan:

```bash
python3 scripts/db/postgres_load_execution_plan.py \
  --load-plan-manifest dist/catalog-manifest-bridge/manifest-import-plan.json \
  --migration-gate-report dist/catalog-manifest-bridge/migration-gate-report.json \
  --output dist/catalog-manifest-bridge/postgres-load-execution-plan.json
```

For catalog manifest bridge loads, the execution planner marks
`readiness.load_ready` false unless the migration gate report is present and
`ok: true`. Blocked plans stop before the schema/load commands.
Ready catalog plans include a post-load read-only probe:

```bash
python3 scripts/db/catalog_operational_view_probe.py \
  --database-url "$DATABASE_URL" \
  --require-database \
  --require-views
```

That probe verifies the catalog operational views are present and populated in
the target database before row-backed consumers treat the load as operationally
ready.

The inverse export planner is:

```bash
python3 scripts/db/catalog_manifest_export_plan.py \
  --row-dir dist/catalog-manifest-bridge \
  --output-dir dist/catalog-manifest-export
```

It reads database-shaped JSONL row sets and writes reviewable manifest YAML to
a separate export directory. It does not overwrite the live catalog.

## Row Mapping

| Manifest field | Database target |
| --- | --- |
| `id` | `component.id`, `component_version.component_id` |
| `type` | `component.type` |
| `version` | `component.version`, `component_version.version` |
| `name` | `component.name` |
| `description` | `component.description` |
| `license` | `component.license` |
| `lifecycle` | `component.lifecycle`, import rotted-context checks |
| `trust_boundary` | `component.trust_boundary` |
| `freshness` | `component.freshness`, import rotted-context checks |
| `created`, `updated` | `component.created`, `component.updated`, import review policy |
| `superseded_by`, `deprecated_on` | `component` lifecycle fields, archive recommendation |
| `attribution`, `links` | `component.attribution`, `component.links` |
| complete manifest | `component.body`, `component_version.body`, `context_object.document` |
| `industry[]` | `component_industry` |
| `capability[]` | `component_capability` |
| `modality[]` | `component_modality` |
| `tags[]` | `component_tag` |
| component-like references | `component_ref` |
| rubric `dimensions[]` | `rubric_dimension` |
| redaction / sensitive-data mask contract | `context_mask_contract` |
| processor inputs, outputs, determinism, implementation, validation, lineage | `context_transformer_contract` |

## Rubrics

Rubrics are database-backed evaluation contracts.

The full manifest remains preserved in `component.body`, but every rubric
dimension gets an indexed row:

```text
rubric_dimension
  rubric_id
  dimension_path
  parent_path
  dimension_level
  label
  weight
  scale
  evidence_required
  gate
  body
```

Hierarchical dimensions use string paths such as:

```text
0.1
1.2
3.4
```

The database view `rubric_dimension_tree` resolves parent dimensions.

## Masks And Transformers

Masks and transformers are database objects, not hard-coded prompt behavior.

The bridge emits two dedicated row families:

```text
context_mask_contract
context_transformer_contract
```

Redaction, PII, PHI, and sensitive-data manifests produce
`context_mask_contract` rows with redaction paths, policy triggers,
entity-type hints, source handles, and lineage back to the seed manifest.

Processor manifests produce `context_transformer_contract` rows from declared
process kind, inputs, outputs, determinism, idempotency, side effects,
implementation target, validation rules, and lineage. This lets processors be
queried as first-class context objects and lets readiness views flag processor
components that have not yet expanded into transformer contracts.

## Components As Context Objects

Every manifest can also become a context object:

```text
component/rubric/baltor-agent-safety-governance-quality
  -> ctx://open-harness-hub/component/rubric/baltor-agent-safety-governance-quality
```

The bridge emits:

```text
context_object
component_context_object
```

This lets rubrics, tools, processors, masks, schemas, adapters, pipelines, and
other catalog entries participate in retrieval, lineage, policy, dimensions,
feedback, and context packs.

## Rotted Context Flags

Import records should flag seed artifacts that need review before they are used
as current operational definitions.

Initial flags:

```text
deprecated_lifecycle
superseded_component
missing_updated_date
volatile_freshness_requires_review
dated_freshness_requires_review
updated_date_review_threshold_days:<n>
version_in_slug_migration_candidate
duplicate_component_id:<id>
duplicate_of:<manifest_path>
```

Flags do not delete files. They produce a recommended action:

```text
import
review
archive_seed
deprecate
supersede
hold
```

Archiving means moving a seed out of the active operational import path after
curator review. It does not mean silently deleting source history.

Duplicate component IDs are held, not imported as duplicate `component` rows.
The import record remains in `manifest_import_record`, but database row
emission is skipped for the duplicate seed until a curator resolves the ID or
archives the duplicate seed.

## Operational Views

The schema provides three bridge views:

```text
catalog_manifest_import_status
component_database_readiness
rubric_dimension_tree
```

Use them to answer:

```text
Which manifests were imported?
Which file hash produced this database version?
Which seed artifacts look stale or deprecated?
Which rubrics still need dimension expansion?
Which components are bound as context objects?
Which components are database-ready?
```

The migration gate checks the same operational assumptions before a load:

```text
row-set counts match the import plan
component IDs are unique
context-object IDs are unique
versions, axes, rubric dimensions, refs, and bindings target known components
context bindings target known context objects
mapped import records equal component rows
duplicate seeds are held instead of loaded twice
review/archive/hold recommendations are explicitly allowed
```

## Export Flow

Database-to-file export should be the inverse path:

```text
component + component_version
  -> manifest envelope
component axis rows
  -> manifest arrays
rubric_dimension rows
  -> dimensions[]
component_ref rows
  -> explicit reference fields, when representable
context-object and policy rows
  -> sidecar export bundle, if not representable in the legacy manifest schema
```

Exports should preserve:

```text
definition_hash
source_ref
component_version_id
exported_at
export_policy
```

The first export foundation uses JSONL row sets as a local stand-in for
database query output:

```text
components.jsonl
component_industries.jsonl
component_capabilities.jsonl
component_modalities.jsonl
component_tags.jsonl
component_refs.jsonl
rubric_dimensions.jsonl
  -> scripts/db/catalog_manifest_export_plan.py
  -> dist/catalog-manifest-export/catalog/**.yaml
  -> manifest-export-plan.json
```

This gives the migration a reversible path before a live Postgres connection is
introduced. The next production step is to replace the JSONL input with queries
against `component`, `component_*`, `rubric_dimension`, and `component_ref`.

The database read/export planner is:

```bash
python3 scripts/db/catalog_db_export_plan.py \
  --row-dir dist/catalog-db-export-rows \
  --sql-output dist/catalog-db-export-rows/export-catalog-db-rows.sql \
  --output dist/catalog-db-export-rows/catalog-db-export-plan.json
```

It emits psql `\copy` SQL that reads:

```text
component
component_version
component_industry / capability / modality / tag
component_ref
rubric_dimension
context_object
component_context_object
context_mask_contract
context_transformer_contract
manifest_import_batch
manifest_import_record
```

and writes the same row-set filenames consumed by
`catalog_manifest_export_plan.py`.

The SQL uses CSV copy mode with control-character delimiter/quote settings so
Postgres does not collapse JSON backslash escaping. It also preserves explicit
`null` values inside `component.body`; those nulls can be schema-significant in
fields such as deterministic `success_criteria`.

## Migration Rule

Do not remove YAML files during the migration.

Use this sequence:

```text
1. Validate manifests.
2. Generate bridge row sets.
3. Review rotted-context flags.
4. Run the migration gate with explicit curator allowances.
5. Probe catalog operational view declarations.
6. Stage rows in Postgres.
7. Probe live catalog operational views after load.
8. Compare database views against static catalog output.
9. Promote Postgres to operational truth.
10. Export database rows back to YAML/Markdown for review and portability.
11. Archive stale seed files only after curator approval.
```

The stable rule is:

```text
Files are reviewable seed/export artifacts.
Database rows are operational truth.
```
