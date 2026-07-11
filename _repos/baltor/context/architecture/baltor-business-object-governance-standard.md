# Baltor Business Object Governance Standard

Every important business object and database object should have a governance
package. This applies to account management objects, billing objects, context
objects, flow objects, connection objects, process objects, identity objects,
policy objects, run objects, integration objects, and analytics objects.

The goal is simple:

```text
No important object should exist as an undocumented table, YAML blob, API
payload, UI card, or background process.
```

Each object type should define:

```text
rubrics
contracts
schemas
layouts
architecture diagrams
required context rules
relationships
dimensions
events
lifecycle
storage mappings
cloud compatibility
policy and security boundaries
```

## Governance Package

For every object type, create an object governance package:

```text
Object Governance Package
  object profile
  lifecycle contract
  API contract
  database contract
  event contract
  context contract
  policy contract
  schemas
  layouts
  architecture diagrams
  required context rules
  relationship rules
  dimension rules
  audit and lineage rules
  rubrics
```

The operational database tables are:

```text
object_governance_profile
object_contract
object_schema_profile
object_layout_profile
object_architecture_diagram
object_context_rule
```

These rows let the product query what each object requires instead of relying
on scattered prose.

## Database Seed Package

The first reviewable database-ready seed package lives at:

```text
db/seeds/object-governance/
```

It includes JSONL examples and a psql load script for the six governance tables:

```text
object_governance_profile.jsonl
object_contract.jsonl
object_schema_profile.jsonl
object_layout_profile.jsonl
object_architecture_diagram.jsonl
object_context_rule.jsonl
load-object-governance-seeds.sql
```

The current seed package is intentionally family-level. It creates baseline
rows for account management, billing, context, flow, connection, process,
database, identity, policy, integration, and analytics object families. The
package also includes first concrete seed files for `tenant`, `membership`,
`billing_account`, `subscription`, `invoice`, `context_object`,
`context_pack`, `source_connection`, `sync_job`, `pack_builder_process`,
`principal`, and `vector_index` across profiles, contracts, schema profiles,
layouts, diagrams, and required context rules.

The next expansion should specialize those concrete baselines where each object
needs a domain-specific API contract, event contract, database schema, UI
layout, or context rule beyond the generic governance baseline.

The current specialized concrete baselines are:

```text
tenant            policy contract + document account schema
membership        security contract + relational membership schema
billing_account   billing contract + relational account schema
subscription      billing contract + relational billing schema
invoice           billing contract + relational billing schema
context_object    context contract + versioned document schema
context_pack      context contract + source-linked pack schema
source_connection integration contract + scoped connection schema
sync_job          event contract + sync timeline schema
pack_builder_process custom process contract + process-run event schema
principal         security contract + identity document schema
vector_index      database contract + vector_metadata schema
```

## Required Object Families

### Account Management Objects

Examples:

```text
tenant
workspace
organization
account
user
team
role
membership
invitation
entitlement
seat_assignment
```

Required context rules:

```text
who owns the account
who can administer it
which tenant/workspace it belongs to
what plan or entitlement applies
what identity provider controls access
what audit trail is required
what data isolation rules apply
```

Required diagrams:

```text
identity and membership graph
tenant/workspace/account hierarchy
role and entitlement state machine
account lifecycle
```

### Billing Objects

Examples:

```text
billing_account
subscription
plan
usage_meter
invoice
credit
payment_method
price_snapshot
pack_usage_record
model_cost_record
```

Required context rules:

```text
which usage events are billable
which usage events are internal only
which price snapshot applied
which customer/account owns the charge
which contract or entitlement overrides pricing
which data can appear in invoice context
which costs are model, storage, retrieval, reranking, or sync costs
```

Required diagrams:

```text
usage-to-invoice flow
subscription state machine
cost allocation data flow
revenue recognition boundary
```

### Context Objects

Examples:

```text
context_object
context_version
context_relationship
context_assertion
context_dimension_definition
context_dimension_value
context_artifact
context_pack
context_lineage_event
```

Required context rules:

```text
every claim has evidence or uncertainty
current state is a pointer, not a mutation
source versions are immutable
relationships are first-class rows
dimension values carry scope, method, confidence, and evidence
packs record retrieval, policy, compression, and lineage
```

Required diagrams:

```text
context object lifecycle
source-to-pack lineage
relationship graph
dimension assessment flow
```

### Flow Objects

Examples:

```text
workflow
flow
pipeline_run
step_run
approval
queue_item
retry
fallback
human_review
```

Required context rules:

```text
which inputs are required
which outputs are expected
which tool/model/ranker versions were used
which step can retry
which step requires approval
which step can write to external systems
which trace links the run to context packs and source handles
```

Required diagrams:

```text
flow DAG
step state machine
retry/fallback path
approval boundary
```

### Connection Objects

Examples:

```text
source_connection
connector
credential_binding
oauth_grant
mcp_server
webhook
sync_job
source_scope
```

Required context rules:

```text
what source is connected
what scopes are granted
what objects can be read
what actions can write
what data can be mirrored, indexed, or link-only
what sync freshness is expected
what happens when credentials expire
```

Required diagrams:

```text
connector trust boundary
credential lifecycle
sync topology
read/write action separation
```

### Process Objects

Examples:

```text
ingestion_process
normalization_process
reranking_process
pack_builder_process
freshness_refresh_process
feedback_process
evaluation_process
deployment_process
```

Required context rules:

```text
which inputs are accepted
which outputs are produced
which transformer contract applies
which policy gates run
which events are emitted
which metrics are tracked
which failure modes are expected
```

Required diagrams:

```text
process sequence diagram
input/output contract
failure mode map
observability map
```

### Database Objects

Examples:

```text
table
view
materialized_view
index
event_stream
partition
warehouse_table
vector_index
graph_index
object_storage_prefix
```

Required context rules:

```text
what is the source of truth
what is derived
what can be rebuilt
what retention applies
what tenant isolation applies
what indexes are promoted
what analytics are wide columnar
what records are append-only
```

Required diagrams:

```text
storage mapping
source-of-truth map
index derivation flow
data retention flow
```

## Required Context Rule Pattern

Every object type should declare rules for:

```text
required_context:
  what context must be loaded before use

forbidden_context:
  what must never be included

freshness:
  what must be current, live validated, or explicitly marked stale

source_precedence:
  which source wins when sources disagree

masking:
  which fields are hidden or projected by role, model, export, or local cache

retrieval:
  how the object can be searched, ranked, expanded, and packed

lineage:
  what source, transformer, model, policy, and user events must be recorded

dimension:
  which scores or assessments are required

relationship:
  which edges must exist or be checked

retention:
  when data expires, tombstones, purges, or enters legal hold
```

## Diagram Standard

Each object family should have at least:

```text
lifecycle diagram
relationship diagram
data-flow diagram
state-machine diagram when stateful
security-boundary diagram when permissions matter
storage-mapping diagram when persisted
```

Mermaid is the default text format for diagrams because it is reviewable in Git
and can be stored as database text.

## Design Rule

The standard for every object:

```text
If it stores money, identity, permissions, context, lineage, source data,
agent actions, customer-visible state, or operational workflow state, it needs
a governance package.
```
