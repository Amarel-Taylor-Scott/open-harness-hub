# Object Governance Seed Package

This directory contains reviewable database-ready seed examples for the object
governance tables in `db/postgres/schema.sql`.

The seed package follows the repository direction:

```text
Markdown/YAML/JSONL are seed, export, and review artifacts.
Postgres rows are operational truth for hosted/runtime systems.
```

## Covered Tables

The package includes one baseline row per required object family for each
governance table:

```text
object_governance_profile.jsonl
concrete_object_governance_profile.jsonl
object_contract.jsonl
concrete_object_contract.jsonl
object_schema_profile.jsonl
concrete_object_schema_profile.jsonl
object_layout_profile.jsonl
concrete_object_layout_profile.jsonl
object_architecture_diagram.jsonl
concrete_object_architecture_diagram.jsonl
object_context_rule.jsonl
concrete_object_context_rule.jsonl
```

Covered object families:

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

The family rows are baseline seeds. The concrete files add the first
object-level rows for `tenant`, `membership`, `billing_account`,
`subscription`, `invoice`, `context_object`, `context_pack`,
`source_connection`, `sync_job`, `pack_builder_process`, `principal`, and
`vector_index` across profiles, contracts, schema profiles, layouts, diagrams,
and context rules. The next expansion should split those baseline rows into
more domain-specific object variants where the generic rows are too broad.

Current concrete object specializations:

```text
tenant            policy contract, document schema, isolation/admin rules
membership        security contract, relational schema, role/revocation rules
billing_account   billing contract, relational schema, payment-reference rules
subscription      billing contract, relational schema, price snapshot rules
invoice           billing contract, relational schema, usage evidence rules
context_object    context contract, document schema, version/source-handle rules
context_pack      context contract, document schema, source-handle rules
source_connection integration contract, relational schema, credential/scope rules
sync_job          event contract, event schema, cursor/freshness rules
pack_builder_process custom process contract, event schema, model-route lineage rules
principal         security contract, document schema, authority/revocation rules
vector_index      database contract, vector_metadata schema, embedding privacy rules
```

## Loading

The generated SQL is a reviewable psql load example:

```bash
psql "$DATABASE_URL" -f db/seeds/object-governance/load-object-governance-seeds.sql
```

The script uses JSONL staging tables and `ON CONFLICT` upserts. Review the rows
before loading them into a shared environment.

## Seed Design Rules

Each seed row should:

- preserve flexible JSONB body fields for long-tail attributes
- declare promoted database fields only where the canonical schema supports them
- use stable object identifiers without embedding a version in the object type
- include lifecycle, policy, cloud, storage, and audit assumptions
- make required context explicit before agents render, bill, sync, retrieve, or
  mutate an object
- use diagrams as database-backed text so they remain reviewable and exportable
