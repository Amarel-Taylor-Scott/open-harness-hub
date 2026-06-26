# Baltor Architecture Context Providers

Architecture tools should feed Baltor as context providers, not become the
whole Baltor layer. Their job is to provide high-quality derived artifacts:
systems, services, owners, dependencies, flows, interfaces, diagrams,
decisions, and architecture summaries. Baltor's job is to normalize those
artifacts into source-linked, versioned, policy-aware context objects and task
packs.

```text
architecture provider
  -> normalized context objects
  -> relationships, claims, dimensions, artifacts, lineage
  -> architecture_pack / implementation_pack / review_pack
  -> Claude Code, Cursor, Copilot, ChatGPT, Rovo Dev, CI agents, humans
```

## Provider Categories

| Category | Examples | Primary contribution |
| --- | --- | --- |
| Architecture model SaaS | IcePanel, Ilograph | Human-curated systems, containers, components, flows, diagrams, dependencies. |
| Architecture-as-code | Structurizr, LikeC4 | Versioned architecture models in Git that can be reviewed in PRs. |
| Diagram renderers | Mermaid, PlantUML, C4-PlantUML, D2, Kroki | Rendered visual artifacts generated from Baltor relationships. |
| Developer portals and service catalogs | Backstage, Port, Compass/DX, Cortex | Ownership, services, APIs, scorecards, documentation links, dependencies. |
| Repo-wiki/code context | DeepWiki, Code Wiki, Swimm, Sourcegraph | Generated repo docs, code summaries, source-linked explanations, diagrams. |
| Event/API catalogs | EventCatalog, AsyncAPI | Event, message, schema, producer, consumer, channel, and impact topology. |
| Enterprise architecture | Ardoq, SAP LeanIX, Bizzdesign | Application portfolios, business capabilities, transformation context, risk. |

## Context Provider Contract

Architecture providers use `provider_type = architecture_context` in
`schemas/context-provider.schema.json`.

Required capabilities should be explicit:

```json
{
  "kind": "baltor.context-provider.v1",
  "provider_id": "provider/icepanel",
  "name": "IcePanel",
  "provider_type": "architecture_context",
  "source_systems": ["icepanel"],
  "capabilities": {
    "discover": true,
    "fetch": true,
    "search": true,
    "relationships": true,
    "permissions": true,
    "artifact_generation": true
  },
  "connector_modes": ["mirrored", "compiled", "link_only"],
  "supported_triggers": ["manual", "scheduled_poll", "pipeline_artifact"],
  "object_types": [
    "architecture_landscape",
    "architecture_domain",
    "architecture_diagram",
    "architecture_component",
    "architecture_connection",
    "architecture_flow",
    "architecture_team"
  ],
  "policy": {
    "acl_filter_before_model": true,
    "raw_source_access": "exact_handle_only",
    "derived_context": true,
    "writes_require_approval": true
  },
  "created_at": "2026-06-02T00:00:00Z"
}
```

## Normalized Object Types

Use generic Baltor object types rather than provider-specific top-level
schema. Provider-specific fields stay in facets.

```text
architecture_landscape
architecture_domain
architecture_system
architecture_container
architecture_component
architecture_connection
architecture_flow
architecture_diagram
architecture_team
architecture_decision
architecture_tag
architecture_version
service_catalog_service
service_catalog_api
event_catalog_domain
event_catalog_service
event_catalog_message
event_catalog_schema
repo_wiki_page
repo_architecture_summary
```

Example source handles:

```text
ctx://acme/icepanel/landscape/{landscape_id}
ctx://acme/icepanel/diagram/{diagram_id}
ctx://acme/icepanel/object/{object_id}
ctx://acme/icepanel/connection/{connection_id}
ctx://acme/icepanel/flow/{flow_id}
ctx://acme/structurizr/workspace/{workspace_id}/element/{element_id}
ctx://acme/likec4/model/{model_id}/view/{view_id}
ctx://acme/backstage/component/{namespace}/{name}
ctx://acme/eventcatalog/service/{service_id}
ctx://acme/asyncapi/{service_id}/channel/{channel}
```

## IcePanel Positioning

IcePanel should be treated as a high-authority architecture context provider.
It is especially useful where teams maintain C4-style systems, containers,
components, flows, tags, teams, and relationships.

Recommended connector shape:

```text
baltor connector icepanel pull
  -> architecture objects
  -> model connections
  -> flows
  -> diagrams
  -> tags
  -> teams
  -> source handles
  -> architecture_pack
```

Baltor should not build an IcePanel clone. Avoid drag-and-drop diagram editing,
manual layout tooling, and whiteboard collaboration as first-order scope.
Baltor should own source handles, lineage, source precedence, conflict and
staleness detection, and policy-aware delivery to agents.

## Pack Usage

`context_for_repo("billing-service")` should include:

```text
service catalog identity
owners and teams
architecture systems/components
dependencies and interfaces
flows and diagrams
repo wiki summaries
event/API relationships
stale or conflicting architecture claims
source handles
```

`context_for_ticket("BILL-782")` should include:

```text
impacted services
linked architecture components
relevant flows
owned APIs/events
decisions and ADRs
dependency risks
freshness warnings
```

`review_pack("MR-4421")` should compare changed files against:

```text
architecture model dependencies
service catalog ownership
event/API producer-consumer topology
repo wiki/code summaries
documented decisions
```

## Architecture Drift

Architecture providers are valuable, but they drift. Baltor should detect:

```text
service in code but missing from architecture model
dependency in code but missing from diagram
diagram references retired service
service catalog owner conflicts with architecture owner
event producer/consumer not represented in architecture context
repo wiki summary contradicts current code
architecture source older than latest relevant MR
```

Drift should become context rows, not just reports:

```text
context_assertion:
  subject = architecture object
  predicate = may_conflict_with
  object = source/code/service catalog object

dimension_value:
  dimension = freshness / verifiability / conflict_level / architecture_risk
```

## First Provider Priorities

P0:

```text
IcePanel
Structurizr
LikeC4
Backstage
EventCatalog
repo-wiki/code-context artifacts
```

P1:

```text
Port
Compass/DX
Cortex
Sourcegraph
Swimm
Mermaid / C4-PlantUML / Kroki renderer
```

P2:

```text
Ardoq
SAP LeanIX
Bizzdesign
Ilograph
Cloudcraft
```

## MVPs

1. IcePanel architecture-pack connector:

```text
IcePanel export/API
  -> architecture objects and relationships
  -> Baltor context objects
  -> architecture_pack
```

2. Context-for-ticket with architecture overlay:

```text
Jira/Linear ticket
  + GitHub/GitLab changed files
  + ADRs
  + IcePanel/Structurizr/LikeC4 architecture
  + Backstage/Port owners
  + EventCatalog/API dependencies
  -> implementation_pack
```

3. Architecture drift detector:

```text
architecture model
  vs code imports/calls/config
  vs service catalog
  vs event/API catalog
  -> architecture_drift_report
  -> context assertions and dimensions
```

4. Generated diagrams from Baltor context:

```text
Baltor relationships
  -> Mermaid / D2 / C4-PlantUML
  -> Kroki-rendered artifact
  -> context_artifact
  -> architecture_pack
```

## Non-Goals

Do not start by building:

```text
diagram editor
whiteboard collaboration
manual C4 layout UI
general-purpose drawing canvas
enterprise architecture portfolio suite
```

The durable Baltor role is:

```text
source handles
context packs
source precedence
claim lineage
architecture-to-ticket linkage
architecture-to-code linkage
staleness and conflict detection
policy-aware delivery to agents
```
