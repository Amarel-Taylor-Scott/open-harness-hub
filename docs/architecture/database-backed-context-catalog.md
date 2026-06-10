# Database-Backed Context Catalog

The repository uses YAML and Markdown because they are easy to review, diff,
publish, and seed. That should not mean the hosted product stores everything as
text files.

The right model is:

```text
YAML / Markdown:
  seed files
  export files
  human-reviewable definitions
  static-site source
  disaster-recovery snapshots

Database:
  operational source of truth
  queryable catalog
  versioned context objects
  relationships
  dimensions
  masks
  transformers
  evaluations
  feedback
  lineage
  analytics
  object governance packages
```

This gives Baltor the best of both: Git-reviewable definitions for the public
catalog and database-backed operations for the product.

## What Should Move To Database Rows

These should be queryable rows, not only YAML fields:

```text
component envelope
component versions
rubric dimensions
rubric evaluations
rubric dimension scores
context objects
context versions
context relationships
context assertions
dimension definitions
dimension values
context artifacts
context packs
lineage events
component-to-context-object bindings
mask contracts
transformer contracts
retrieval events
feedback events
usage/cost/freshness analytics
object governance profiles
object contracts
object schema profiles
object layout profiles
object architecture diagrams
object context rules
```

YAML can still export/import those records, but the running product should not
parse hundreds of files to answer operational questions.

## Why Rubrics Should Be Database Entries

Rubrics are not static prose. They are evaluation contracts.

Database rows let the product answer:

```text
Which rubrics apply to this context pack?
Which dimensions failed across the last 100 reviews?
Which dimensions are gates?
Which evidence packets were attached?
Which score changed after a transformer or reranker update?
Which customer pilots fail cloud-portability dimensions?
Which fragile-information dimensions are improving?
```

The Postgres schema now includes:

```text
rubric_dimension
rubric_evaluation
rubric_dimension_score
```

The full rubric manifest can remain in `component.body`, while dimensions and
scores become query-friendly rows.

## Components As Context Objects

Tools, rubrics, masks, transformers, schemas, processors, prompts, adapters,
and pipelines should be represented as context objects when they participate in
retrieval, policy, lineage, or evaluation.

The Postgres schema now includes:

```text
object_governance_profile
object_contract
object_schema_profile
object_layout_profile
object_architecture_diagram
object_context_rule
component_context_object
context_mask_contract
context_transformer_contract
```

The reviewable seed package lives at:

```text
db/seeds/object-governance/
```

It includes family-level governance rows, first concrete object rows across all
six governance tables, and a psql loader. The registry helper is:

```text
python3 scripts/db/object_governance_registry.py --format markdown
python3 scripts/db/object_governance_registry.py --check-seed-coverage
```

Hosted deployments should load those rows into Postgres and treat the database
as operational truth. The JSONL files remain seed/export/review artifacts.

The canonical schema exposes object-governance readiness through database
views:

```text
object_governance_profile_readiness
object_governance_family_coverage
object_governance_specialization_status
```

These views let hosted admin surfaces and agents query whether every object
profile has companion contract, schema, layout, diagram, and context-rule rows,
and whether concrete object rows are still generic or specialized.

The local admin demo keeps a schema/JSONL fallback, but when `DATABASE_URL` is
configured and a compatible Postgres driver is installed, the operational
readiness payload probes these views directly and reports their row counts.

Operators can run the same check outside the admin server:

```bash
python3 scripts/db/object_governance_view_probe.py
DATABASE_URL="$DATABASE_URL" python3 scripts/db/object_governance_view_probe.py --require-database
```

For local Postgres smoke testing, generate a reviewed command plan instead of
running mutating database steps directly:

```bash
python3 scripts/db/object_governance_local_postgres_smoke_plan.py
python3 scripts/db/object_governance_local_postgres_smoke_plan.py --self-test
```

The plan chains local Postgres startup, schema initialization, object-governance
seed loading, seed coverage validation, and live view probing. It is
side-effect-free until an operator reviews and runs the emitted commands.

This lets a catalog component bind to a context object:

```text
component/rubric/baltor-agent-safety-governance-quality
  -> context_object ctx://baltor/rubric/agent-safety-governance-quality

component/processor/contextual-parse
  -> context_object ctx://baltor/transformer/raw-to-normalized/contextual-parse

component/tool/context_fetch
  -> context_object ctx://baltor/tool/context_fetch

mask pii-redaction-view
  -> context_object ctx://baltor/mask/pii-redaction-view

rubric dimension 3.2
  -> context_object ctx://open-harness-hub/component/rubric/.../rubric-dimension/3.2
```

The binding row records the role:

```text
is_context_object
describes
evaluates
masks
transforms
calls
routes
indexes
packs
governs
implements
has_rubric_dimension_context
```

The catalog manifest bridge emits context objects for rubric dimensions and
binds them with `has_rubric_dimension_context`. It also emits loadable
`context_mask_contracts.jsonl` and `context_transformer_contracts.jsonl` row
sets. Processor manifests populate `context_transformer_contracts.jsonl` from
declared `process_kind`, inputs, outputs, determinism, idempotency,
side-effect, implementation, validation, and lineage fields. Redaction, PII,
PHI, and sensitive-data manifests populate `context_mask_contracts.jsonl` with
redaction paths, policy triggers, entity-type hints, and source handles. Other
mask kinds such as projection, permission, local-sync, export, and summary-view
masks should be added only when seed/export artifacts declare those contracts
explicitly.

The reverse path is also part of the migration contract. Generated row sets can
be exported back to reviewable manifest YAML with:

```bash
python3 scripts/db/catalog_manifest_export_plan.py \
  --row-dir dist/catalog-manifest-bridge \
  --output-dir dist/catalog-manifest-export
```

The export report includes row-source status so reviewers can distinguish
seed-bridge exports, database-exported rows, and stale or not-ready snapshots.
The database migration smoke runs this export step from seed rows and writes
review artifacts under `dist/catalog-migration-smoke/manifest-export-from-seed-rows/`.
Those generated files are portability/review/static-site artifacts; they do not
replace the live `catalog/` manifests and should not become the hosted runtime
read path after database promotion.

## Masks As Database Objects

A mask should not be an invisible function or prompt instruction. It should be
a context object plus a contract row.

Examples:

```text
redaction mask:
  removes secrets, PII, customer identifiers, tokens

projection mask:
  shows only fields allowed for a user, agent, export, local cache, or model
  destination

summary view mask:
  allows summarized content but denies raw source expansion

local sync mask:
  controls what can be saved into private encrypted local memory
```

The `context_mask_contract` table stores:

```text
mask_kind
target_types
include_paths
exclude_paths
redact_paths
policy_trigger
redaction_reason
reversible
contract
```

## Transformers As Database Objects

A transformer changes representation. Examples:

```text
raw Jira JSON -> normalized work item
Confluence page -> normalized Markdown
normalized document -> chunks
chunk -> claim
artifact -> embedding
retrieval candidates -> reranked list
objects/artifacts -> context pack
context pack -> UI view
```

The `context_transformer_contract` table stores:

```text
transformer_kind
input_contract
output_contract
deterministic
model_required
lossiness
reversible
validation
lineage_policy
contract
```

This matters because transformers can introduce errors, omit evidence, leak
data, or change authority. They need versioning, lineage, validation, and
rollback.

## Operational Flow

Use this flow for the hosted product:

```text
1. Load YAML manifests as seed/import records.
2. Upsert component rows.
3. Upsert component_version rows with definition hashes.
4. Expand rubric dimensions into rubric_dimension rows.
5. Bind components to context_object rows where they participate in context.
6. Store object governance profiles, contracts, schemas, layouts, diagrams, and context rules.
7. Store mask and transformer contracts as queryable rows.
8. Generate context packs, evaluations, feedback, and lineage as append-only rows.
9. Export selected database rows back to YAML/Markdown for static docs and Git review.
```

The concrete seed/import bridge is documented in
[`catalog-manifest-database-bridge.md`](catalog-manifest-database-bridge.md).
Use `scripts/db/catalog_manifest_bridge.py` to generate reviewable JSONL row
sets and a psql load script from validated catalog manifests. The bridge also
emits manifest import records so stale, deprecated, superseded, volatile, or
version-in-slug seed artifacts can be reviewed and archived without deleting
catalog history.

Run `scripts/db/catalog_manifest_migration_gate.py` before applying the load
SQL. The gate checks row-set integrity and fails closed unless hold, review, or
archive recommendations are explicitly allowed for the current batch. This
keeps YAML as seed input instead of letting stale files silently become
operational truth.

Use `scripts/db/catalog_manifest_export_plan.py` for the inverse dry-run path:
database-shaped row sets back to reviewable YAML exports in a separate output
directory. This makes the migration reversible before a live Postgres export
worker is connected.

Use `scripts/db/catalog_db_export_plan.py` once rows have been loaded into
Postgres. It emits psql copy SQL that reads the operational database tables
back into the same JSONL row shape, then the manifest exporter can produce
reviewable YAML from database truth instead of YAML-derived rows.
The export plan includes an integrity-validation command that must pass before
row-backed consumers or manifest exports use the exported rows.
Round-trip parity reports include content fingerprints for every registered row
family. The staleness gate and refresh planner regenerate parity when those
fingerprints do not match the current seed/export row directories, preventing a
stale parity report from hiding newly imported context objects, mask contracts,
or transformer contracts.
The refresh planner also emits the hard post-refresh gates: row integrity,
schema coverage, round-trip parity, non-advisory staleness gating,
non-advisory promotion readiness, and a manifest export from database rows into
a separate review directory. These gates should pass before hosted consumers
prefer database rows over YAML fallback.

`scripts/processors/catalog_search.py` is the first consumer with a
database-row read path. It still supports catalog YAML for static/local use,
but hosted or smoke-test flows can pass:

```bash
python3 -m scripts.processors.catalog_search \
  --row-dir dist/catalog-db-export-rows-smoke \
  --prompt "I need a pipeline to grade an ESG supplier disclosure"
```

Use `scripts/db/catalog_row_source_compare.py` to compare search behavior over
YAML-derived bridge rows and database-exported rows before switching more
consumers away from direct YAML walking.

Use `scripts/db/catalog_row_source.py` as the shared row-source loader for
consumer scripts. It centralizes how `components.jsonl`, axis row sets, source
paths, and `component_refs.jsonl` are interpreted so database-backed consumers
do not drift into slightly different manifest-to-row mappings.

Run `scripts/db/catalog_row_integrity.py` on any row directory before treating
it as operational truth:

```bash
python3 scripts/db/catalog_row_integrity.py \
  --row-dir dist/catalog-db-export-rows-smoke \
  --output dist/catalog-db-export-rows-smoke/catalog-row-integrity-report.json
```

This validator checks row-set structure, component identity, version coverage,
context-object bindings, component references, rubric dimensions, and duplicate
axis rows without reading live catalog YAML. It complements the migration gate:
the gate handles seed/import policy allowances, while the integrity validator
proves a row snapshot is safe for row-backed consumers.

Use `scripts/db/catalog_row_schema_coverage.py` to prove that every emitted row
family has a matching canonical Postgres table and generated load-SQL path:

```bash
python3 scripts/db/catalog_row_schema_coverage.py \
  --row-dir dist/catalog-manifest-bridge \
  --output dist/catalog-migration-smoke/catalog-row-schema-coverage.json
```

This coverage check ties together the JSONL row family, `manifest-import-plan`
count, `load-catalog-manifests.sql` copy/insert references, and
`db/postgres/schema.sql`. It is intentionally separate from row-level integrity:
integrity proves rows are internally safe; schema coverage proves the
seed/export bridge has a destination in the operational database contract.

The bridge import plan itself also records `load_sql_coverage`. This is the
first preflight check in the seed-to-database direction: it verifies that every
generated row file is referenced by `load-catalog-manifests.sql`, has a matching
stage name, and contributes to the expected load statement count. Keep this
symmetrical with `export_sql_coverage` in `catalog_db_export_plan.py`; together
they make omissions in contract row families visible before a live database
refresh is trusted.

After bridge rows are loaded into Postgres and exported again, use
`scripts/db/catalog_row_roundtrip_parity.py` to compare seed-derived rows with
database-exported rows:

```bash
python3 scripts/db/catalog_row_roundtrip_parity.py \
  --seed-row-dir dist/catalog-manifest-bridge \
  --db-row-dir dist/catalog-db-export-rows \
  --output dist/catalog-migration-smoke/catalog-row-roundtrip-parity.json
```

This is stricter than search comparison: it compares canonical JSON row hashes
for every import/export row family except run-specific import ledger rows. It
should be run after a fresh database export, not against stale smoke snapshots.
Mismatches mean the operational database export no longer round-trips the
reviewed seed/export contract.

The database export planner also checks its generated SQL coverage before a
live database is involved:

```bash
python3 scripts/db/catalog_db_export_plan.py \
  --row-dir dist/catalog-db-export-rows-smoke \
  --sql-output dist/catalog-db-export-rows-smoke/export-catalog-db-rows.sql \
  --output dist/catalog-db-export-rows-smoke/catalog-db-export-plan.json
```

The resulting plan contains `export_sql_coverage`, including the expected row
family count, generated `\copy` count, and a per-family file/path reference
check. This prevents contract row families such as context mask contracts,
transformer contracts, rubric dimensions, and component context bindings from
being added to the seed bridge but accidentally omitted from database export.

When parity fails against a stale smoke export, use
`scripts/db/catalog_db_export_smoke_refresh_plan.py` to produce the concrete
reload/export/verify sequence:

```bash
python3 scripts/db/catalog_db_export_smoke_refresh_plan.py \
  --bridge-dir dist/catalog-manifest-bridge \
  --db-row-dir dist/catalog-db-export-rows-smoke \
  --output dist/catalog-migration-smoke/catalog-db-export-smoke-refresh-plan.json
```

This planner is intentionally side-effect free. It does not run Postgres; it
records the exact commands for rebuilding bridge rows, applying the schema,
loading rows, probing live catalog operational views, exporting database rows,
validating integrity and schema coverage, and rerunning round-trip parity. This
keeps stale smoke snapshots visible without weakening the no-Postgres migration
smoke.

Use `scripts/db/catalog_db_export_staleness_gate.py` when a job needs to block
promotion of stale database-exported rows:

```bash
python3 scripts/db/catalog_db_export_staleness_gate.py \
  --seed-row-dir dist/catalog-manifest-bridge \
  --db-row-dir dist/catalog-db-export-rows-smoke \
  --parity-report dist/catalog-migration-smoke/catalog-row-roundtrip-parity.json \
  --output dist/catalog-migration-smoke/catalog-db-export-staleness-gate.json
```

Without `--advisory`, the gate exits non-zero when round-trip parity has
blocking errors. With `--advisory`, it records `would_pass: false` but exits
successfully; the dry-run migration smoke uses advisory mode because it cannot
refresh Postgres itself. Promotion or release jobs should omit `--advisory`
after refreshing the database-exported row snapshot.

Use `scripts/db/catalog_database_promotion_readiness.py` as the rollup gate
after a local or staging database refresh:

```bash
python3 scripts/db/catalog_database_promotion_readiness.py \
  --bridge-dir dist/catalog-manifest-bridge \
  --db-row-dir dist/catalog-db-export-rows-smoke \
  --smoke-dir dist/catalog-migration-smoke \
  --output dist/catalog-migration-smoke/catalog-database-promotion-readiness.json
```

This report combines bridge generation, seed load-SQL coverage, post-load
catalog view probe planning, seed row integrity, seed schema coverage, database
export-SQL coverage, database export row integrity, and round-trip staleness.
In dry-run smoke it runs with `--advisory`; for promotion jobs, omit
`--advisory` so stale or incomplete database-exported rows, or a generated load
plan that does not probe live catalog views, fail before they can be treated as
operational truth.

Row-backed consumers should surface row-source status from
`scripts/db/catalog_row_source.py` when they produce user-facing or
machine-consumed artifacts. The status metadata is advisory and non-blocking:
it reports whether the row directory looks like seed-bridge rows,
database-export rows, or an unknown snapshot, and links to integrity,
staleness, and promotion-readiness reports when present. This makes stale
database exports visible in search/index artifacts without forcing
local/static fallback consumers to fail.

Use `scripts/db/catalog_database_migration_smoke.py` as the dry-run checklist
for the full seed/export migration path:

```bash
python3 scripts/db/catalog_database_migration_smoke.py \
  --output dist/catalog-migration-smoke/catalog-database-migration-smoke.json
```

The smoke script regenerates bridge rows, runs the migration gate with explicit
current allowances, validates bridge and database-exported row integrity,
validates bridge row-family schema coverage, generates load/export plans,
audits remaining direct YAML readers, compares row-backed search behavior,
renders row-backed catalog docs, and builds the row-backed browser index and
SQLite snapshot. It does not connect to Postgres, start Docker, mutate live
catalog files, or prove a live database was loaded.

Use `scripts/db/catalog_yaml_reader_audit.py` when you only need the direct
YAML-reader inventory:

```bash
python3 scripts/db/catalog_yaml_reader_audit.py \
  --output dist/catalog-migration-smoke/catalog-yaml-reader-audit.json
```

The audit classifies readers as seed/export validation, seed/export bridge,
row-backed consumer, draft generation, data JSONL utility, documentation/example,
or operational migration candidate. Operational candidates should either gain a
`catalog_row_source.py` read path or be explicitly reclassified as
seed/export-only.

`scripts/build_catalog_db.py` also has a database-row read path for the
portable SQLite catalog snapshot:

```bash
python3 scripts/build_catalog_db.py \
  --row-dir dist/catalog-db-export-rows-smoke \
  --output dist/catalog-from-db.sqlite
```

The legacy no-argument mode still walks catalog YAML for static/local
bootstrap, but row-backed builds should be preferred for hosted snapshots. This
makes SQLite a cache/export of database truth instead of another operational
YAML reader. Duplicate seed IDs are skipped in the legacy YAML snapshot and
should be reviewed through the migration gate, where they are recorded as
held import records. The SQLite snapshot also writes
`catalog_snapshot_metadata`, including the source kind, row directory, and
advisory `row_source_status` payload. Row-backed consumers can inspect this
metadata before trusting a database-exported snapshot that may still be stale
or not promotion-ready.

`scripts/build_catalog_pages.py` has the same row-source pattern for rendered
catalog documentation:

```bash
python3 scripts/build_catalog_pages.py \
  --row-dir dist/catalog-db-export-rows-smoke \
  --output-dir dist/catalog-pages-from-db
```

The default mode still renders from YAML seed/export files for local static
site workflows. Hosted or smoke-test documentation builds should prefer
database-exported rows so the pages reflect operational catalog truth and can
show exported database relationships. When `--row-dir` is used, the generated
`index.md` includes a row-source status section with promotion, staleness, and
integrity fields so human readers can see when pages were rendered from a stale
or not-ready database export.

`scripts/build_catalog_index.py` also supports database-exported rows for the
static browser `index.json`:

```bash
python3 scripts/build_catalog_index.py \
  --row-dir dist/catalog-db-export-rows-smoke \
  --output dist/catalog-migration-smoke/index-from-db-rows.json
```

The YAML fallback can include held duplicate seed manifests. Row-backed browser
indexes reflect the operational row set after migration-gate handling.

`scripts/oh_hub.py` can read the same database-exported row sets for human and
agent CLI access:

```bash
python3 scripts/oh_hub.py \
  --row-dir dist/catalog-db-export-rows-smoke \
  stats
```

The default mode still reads YAML seed/export manifests for local bootstrap.
Hosted, smoke-test, or product-facing CLI flows should use `--row-dir` or set
`OH_CATALOG_ROW_DIR` so catalog lookups, search, dependency inspection, and
descriptions reflect database truth. The `run` command still delegates to
`scripts/run_pipeline.py`, which now accepts the same row-source option:

```bash
python3 scripts/run_pipeline.py \
  --row-dir dist/catalog-db-export-rows-smoke \
  pipeline/recommend-pipeline-from-prompt \
  --simulate
```

Pipeline traces include `catalog_source` so smoke runs and audit logs can show
whether execution came from `database_rows` or `catalog_yaml_seed_export`.
Runtime pipeline execution should use row mode in hosted paths; YAML mode is a
local/static bootstrap fallback until the live database service replaces row
snapshots.

`scripts/factory/processor_loader.py` follows the same boundary for runtime
processor resolution. Hosted orchestrators should list and resolve processors
from exported rows rather than walking `catalog/processors` directly:

```bash
python3 -m scripts.factory.processor_loader \
  --row-dir dist/catalog-db-export-rows-smoke \
  --list

python3 -m scripts.factory.processor_loader \
  --row-dir dist/catalog-db-export-rows-smoke \
  --resolve processor/catalog-search
```

The YAML path remains available for local bootstrap and static development, but
database-row mode is now part of the migration smoke suite so callable
resolution cannot silently drift back to catalog files.

`scripts/factory/capability_lift_gate.py` also supports row-backed scoring for
catalog-quality and novelty review:

```bash
python3 -m scripts.factory.capability_lift_gate \
  --row-dir dist/catalog-db-export-rows-smoke \
  --report dist/catalog-migration-smoke/capability-lift-gate-from-db-rows.json
```

The report includes `catalog_source` and `row_dir` so reviewers can distinguish
database truth from seed/export fallback. Destructive `--apply` mode is disabled
for database-row scans; row-backed runs should produce review/export decisions,
not delete catalog files.

`scripts/factory/capability_gap_scout.py` uses row-backed knowledge-pack names
for deduping proposed gaps against the live catalog:

```bash
python3 -m scripts.factory.capability_gap_scout \
  --row-dir dist/catalog-db-export-rows-smoke \
  --self-test
```

The scout still reads discovered-candidate JSONL history from
`data/capability-gaps`, but the live catalog side of dedup should come from
database rows in hosted runs. YAML knowledge-pack scanning remains a local
seed/export fallback.

`scripts/foundry/standardize.py` does not use catalog files as runtime
operational truth, but its offline self-test needs a known-good manifest to
prove canonical schema validation still works. That sample now comes from
database rows when a row directory is available:

```bash
OH_CATALOG_ROW_DIR=dist/catalog-db-export-rows-smoke \
python3 -m scripts.foundry.standardize
```

YAML remains the fallback only for local seed/export bootstrap when row exports
are not present. The migration smoke includes a `foundry_standardize_database_rows`
step so this validation proof cannot silently regress to catalog-file reads.

Standards emitters under `scripts/emit/` share `scripts/emit/_lib.py`, which
also reads database-exported rows when `OH_CATALOG_ROW_DIR` is set:

```bash
OH_CATALOG_ROW_DIR=dist/catalog-db-export-rows-smoke \
python3 scripts/emit/spdx_3.py
```

`oh-hub --row-dir ... emit ...` forwards the same environment variable to the
selected emitter. This keeps existing emitter command shapes stable while
making SPDX, CycloneDX, MCP, Hugging Face, Promptfoo, Croissant, OpenLineage,
and related export surfaces consume database truth in hosted/export flows.

Vector artifacts should also build from database-exported rows in hosted flows:

```bash
python3 scripts/db/build_vector_index.py \
  --row-dir dist/catalog-db-export-rows-smoke \
  --embedder hash \
  --output-dir dist/catalog-migration-smoke/vector-index-from-db-rows

python3 -m scripts.db.build_vector_store \
  --row-dir dist/catalog-db-export-rows-smoke \
  build \
  --store dist/catalog-migration-smoke/vector-store-from-db-rows.sqlite \
  --model hash-bow-v1 \
  --limit 400
```

The hash embedder remains an offline placeholder for migration and smoke tests.
Promotable hosted builds can use the configured embedding backend while keeping
the same row-source boundary. YAML mode remains available for local seed/export
bootstrap only. The vector index `_meta.json`, vector-store build report, and
`vector_store_metadata` table include `row_source_status` when built from
database-shaped rows, so vector consumers can detect seed bridges,
database-export rows, and stale or not-ready row snapshots before trusting a
cache.

The Postgres schema includes three operational bridge views:

```text
catalog_manifest_import_status
component_database_readiness
rubric_dimension_tree
```

These views should become the normal product surface for answering whether a
manifest is imported, current, database-ready, expanded into rubric dimensions,
bound as a context object, and expanded into mask or transformer contracts.
`component_database_readiness` reports `mask_contract_count` and
`transformer_contract_count`; processor components without transformer
contracts surface as `processor_transformer_contract_not_expanded`.

## What Should Stay In Files

Files still make sense for:

```text
public catalog seed manifests
schema definitions
documentation
examples
reviewable proposed changes
static site content
offline bootstrap
signed exports
```

The rule should be:

```text
Files are review and portability artifacts.
Database rows are operational truth.
```

## Product Implication

This database-backed model lets Baltor move beyond a static catalog:

```text
query all failed rubric dimensions
track fragile information freshness
compare pack quality over time
audit what an agent saw
rank masks and transformers by failure rate
measure cost per pack
find stale context objects
link tools, masks, transformers, and rubrics into the context graph
export clean YAML snapshots for review
```
