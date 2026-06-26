# Baltor Context Object Graph Profile

Updated: 2026-06-01

This profile stores the broader context-object design for deployments that need
relationships, versioning, history, lineage, retrieval indexes, and agent
delivery. The target is not one database product. The target is a portable
contract that can be projected into Markdown, Git, Postgres, graph databases,
vector databases, search engines, object stores, SaaS enterprise search,
Atlassian/Rovo-centered work graphs, regulated enclaves, or local developer
memory.

## Core Model

The core records are:

| Record | Purpose |
| --- | --- |
| `baltor.context-object` | Stable identity for a context object. |
| `baltor.context-version` | Immutable observed state of a context object. |
| `baltor.context-artifact` | Immutable derived representation such as chunk, claim, summary, embedding, repo wiki page, or pack. |
| `baltor.context-relationship` | Typed directional edge between objects, versions, or artifacts. |
| `baltor.context-assertion` | Source-linked statement about an object, relationship, dimension, or flexible attribute. |
| `baltor.context-dimension-definition` | Registry entry for scored or classified dimensions such as risk, verifiability, freshness, and actionability. |
| `baltor.context-dimension-value` | Versioned dimension assessment for an object, artifact, relationship, assertion, or pack. |
| `baltor.context-event` | Append-only lineage, history, audit, retrieval, and feedback event. |
| `baltor.context-pack` | Task-specific delivery bundle for an agent or application. |

Current schema files:

```text
schemas/context-object.schema.json
schemas/context-version.schema.json
schemas/context-artifact.schema.json
schemas/context-relationship.schema.json
schemas/context-assertion.schema.json
schemas/context-dimension-definition.schema.json
schemas/context-dimension-value.schema.json
schemas/context-event.schema.json
schemas/context-pack.schema.json
```

## Flexible Facets, 5W1H, and Dimensions

The object envelope stays small and stable, while long-tail attributes live in
namespaced `facets` such as `core`, `baltor.claim`, `baltor.connector`,
`jira`, `gitlab`, `healthcare.fhir`, or `custom.<team>`. High-value attributes
can be promoted into indexed fields or first-class dimension assessments
without changing every object schema.

Every context object may also include a `five_w_one_h` projection:

```text
who    actors, owners, reviewers, audience
what   entities, topics, object types
when   observed, valid, source, expiry, and refresh dates
where  digital, logical, and physical locations
why    goals, rationale, and drivers
how    methods, processes, and tools
```

Risk, verifiability, authority, freshness, sensitivity, prompt-injection risk,
and actionability are modeled as `baltor.context-dimension-value` records.
Scores are assessments, not source facts. They carry scope, evidence, method,
confidence, and validity windows. Flexible attributes that need evidence,
confidence, or conflict handling should be represented as
`baltor.context-assertion` records rather than fragile inline fields.

## Layering

Context should not be stored only as chunks. A durable context database should
separate source truth from derived context:

```text
L0 raw source snapshot
L1 normalized canonical representation
L2 structural chunks
L3 extracted claims, decisions, facts, requirements, and constraints
L4 summaries, generated repo wikis, ticket packs, and MR packs
L5 task-specific context packs
L6 runtime memory, feedback, and usage traces
```

Agents should usually receive L5, sometimes L4 or L3, rarely L2, and almost
never L0.

## Versioning Rules

- Source versions are immutable.
- Derived artifacts are immutable.
- Embeddings are immutable and tied to model, dimension, chunk strategy, and
  source artifact.
- Summaries are immutable and tied to source versions, model, and prompt
  version.
- Context packs are immutable and tied to retrieval events.
- ACL changes create a new security facet or ACL hash.
- Relationship changes create new edge records or validity windows.
- Deletes create tombstones unless policy requires hard deletion.
- `current_version_id` is a pointer. It is not history mutation.

## Relationship Vocabulary

Common relationship types:

```text
CONTAINS
PART_OF
DERIVED_FROM
CITES
SUPPORTS
CONTRADICTS
SUPERSEDES
MAY_SUPERSEDE
DEFINES
ALIAS_OF
MENTIONS
IMPLEMENTS
FIXES
DEPENDS_ON
BLOCKS
OWNED_BY
APPROVED_BY
APPLIES_TO
GENERATED_BY
OBSERVED_AT
AFFECTS
REQUIRES_REFRESH
```

Ownership and corporate-history relationship types:

```text
ACQUIRED
MERGED_INTO
SPLIT_FROM
SPUN_OUT_FROM
CURRENT_PARENT_OF
FORMER_PARENT_OF
CONTRADICTS
SUPERSEDES
REQUIRES_REFRESH
```

Relationships are directional, source-backed, confidence-scored, and
time-aware. They should include `valid_from` and `valid_to` when time matters.

## Policy Rules

- Derived context inherits the strictest policy of its sources.
- Raw source dumps are not durable context objects unless explicitly classified
  as raw snapshots.
- Durable claims require `ctx://` source handles.
- Promotion into global memory or a canonical graph is blocked until source,
  ACL, freshness, and conflict policies allow it.
- User-generated content from tickets, comments, emails, chats, and external
  sites is untrusted source data, not instructions.

## Retrieval Projections

The same context records can be projected into multiple serving systems:

| Projection | Use |
| --- | --- |
| Object store | Raw snapshots and normalized artifacts. |
| Postgres | Metadata, versions, policies, events, and edge tables. |
| Graph database | Relationship traversal and impact analysis. |
| Search index | Keyword, exact identifiers, paths, error strings, and citations. |
| Vector index | Semantic candidate retrieval. |
| Cache | Hot context packs and local/offline packs. |
| MCP resources/tools | Agent delivery. |

Pure vector storage is not a context database. It is one projection.

## Deployment Variants

The same profile should work across:

- local Markdown or Obsidian memory;
- repo-level context-as-code and generated repo wikis;
- Atlassian/Rovo-centered Jira and Confluence work context;
- enterprise MCP gateways and portals;
- enterprise search and SaaS retrieval platforms;
- custom graph plus RAG deployments;
- data catalog and lakehouse deployments;
- regulated enclaves for healthcare, finance, legal, HR, defense, or security;
- cross-organization or industry exchange using standards such as FHIR,
  ISO 20022, XBRL/iXBRL, STIX/TAXII, GS1 EPCIS, IFC, OPC UA, SPDX, and
  CycloneDX where applicable.

## Lifecycle

Every important context state transition should be represented by a
`baltor.context-event` record:

```text
DISCOVERED
FETCHED
NORMALIZED
CLASSIFIED
PERMISSIONED
CHUNKED
EMBEDDED
LINKED
SUMMARIZED
INDEXED
RETRIEVED
SERVED
EXPANDED
VALIDATED
CORRECTED
SUPERSEDED
RETIRED
TOMBSTONED
FEEDBACK_RECEIVED
POLICY_DENIED
```

This makes it possible to answer:

- What did the agent see?
- Which version did it use?
- Was that version current?
- Was the user allowed to see it?
- Which model or pipeline compressed it?
- Which sources were omitted, redacted, or superseded?
- Would the answer be different now?

## First Implementation Target

The first implementation should not attempt every backend. It should expose the
schema family and use it to harden the existing Baltor gateway:

```text
context_schema_catalog()
context_object_schema()
context_search()
context_fetch()
context_trace()
context_sync_contracts()
```

Then add storage in this order:

1. JSON Schemas and docs.
2. Context pack and cache manifests.
3. Version/artifact/relationship/event exports in the admin demo.
4. Assertion and dimension exports for flexible facets, 5W1H projections,
   risk, verifiability, freshness, and actionability.
5. Postgres tables for objects, versions, artifacts, relationships, assertions,
   dimensions, and events.
6. Search/vector projections.
7. Graph traversal and lineage queries.
