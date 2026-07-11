# Baltor Context Fabric Product Blueprint

Updated: 2026-06-01

Baltor Context Fabric is a governed context-object platform for humans, agents,
and enterprise systems. It should not be positioned as a chatbot over documents
or a thin vector database wrapper. The product promise is:

```text
Any agent can ask for context.
Context Fabric returns the smallest safe, source-linked, versioned,
policy-compliant context object or context pack needed for the task, with
relationships, history, lineage, and evidence intact.
```

## Product Definition

Context Fabric provides:

```text
connectors
  -> context object normalization
  -> versioning and lineage
  -> relationship graph
  -> permissions and policy
  -> retrieval and indexing
  -> token compression
  -> MCP/API delivery
  -> evals, feedback, and governance
```

It complements rather than replaces systems such as Rovo, Jira, Confluence,
GitLab, GitHub, DeepWiki-style repo wikis, Obsidian, Glean, Onyx, Sourcegraph,
Cloudflare AI Search, Qdrant, Weaviate, Pinecone, OpenSearch, and internal data
catalogs.

## Product Planes

| Plane | Purpose |
| --- | --- |
| Source plane | Connect to systems of record and generated context sources. |
| Object plane | Convert source records into durable context objects, versions, and artifacts. |
| Relationship plane | Link issues, docs, code, incidents, decisions, people, data, and artifacts. |
| Retrieval plane | Build indexes, rerank, compress, and assemble context packs. |
| Control plane | Govern identity, ACLs, policy, lineage, audit, evals, and deployment. |

## Product Modules

1. Context connectors
   - Rovo/Jira/Confluence
   - GitLab/GitHub/Bitbucket
   - DeepWiki/OpenDeepWiki/RepoWiki/Reporecall style repo wiki providers
   - Obsidian/Markdown/local memory
   - Slack/Teams/email
   - enterprise search such as Onyx/Glean
   - observability, CI/CD, support, CRM, data/BI, security, legal, healthcare,
     manufacturing, supply chain, and AEC systems

2. Context object registry
   - `ctx://` identifiers
   - native source ID mapping
   - current version pointers
   - object ownership and stewardship
   - classification, ACL, and retention metadata

3. Versioning and history
   - immutable source versions
   - immutable derived artifacts
   - immutable embeddings tied to model and chunk strategy
   - context packs tied to retrieval and compression events
   - relationship validity windows
   - tombstones instead of silent deletion

4. Context graph
   - work graph
   - code graph
   - decision graph
   - data graph
   - incident graph
   - industry graph

5. Artifact engine
   - raw snapshots
   - normalized records
   - structural chunks
   - claims
   - decisions
   - summaries
   - embeddings
   - repo wiki pages
   - context packs
   - redacted views

6. Policy and permissions
   - OIDC/OAuth identity
   - source permissions
   - context permissions
   - local memory promotion policy
   - model destination policy
   - DLP and redaction
   - retention and legal hold
   - write/action approval

7. Retrieval and indexing
   - exact handle fetch
   - keyword/BM25
   - dense vector
   - sparse vector
   - hybrid search
   - graph traversal
   - temporal retrieval
   - source precedence
   - conflict detection
   - reranking

8. Context pack builder
   - `implementation_pack`
   - `review_pack`
   - `debugging_pack`
   - `incident_pack`
   - `architecture_pack`
   - `compliance_pack`
   - `clinical_summary_pack`
   - `security_triage_pack`
   - `legal_matter_pack`
   - `supply_chain_trace_pack`

9. Agent interfaces
   - MCP tools/resources
   - REST/GraphQL
   - A2A for multi-agent workflows
   - webhooks
   - SDKs
   - CLI
   - CI/CD integrations

10. Observability, evals, and feedback
    - OpenTelemetry-style traces
    - source recall and precision
    - citation coverage
    - permission-denial tracking
    - stale-source rate
    - conflict-detection rate
    - token and cost metrics
    - human feedback and promotion decisions

## Product Schemas

The product-level contracts are:

```text
_repos/shared-backend-components/schemas/context-product-surface.schema.json
_repos/shared-backend-components/schemas/context-provider.schema.json
_repos/shared-backend-components/schemas/context-pack-builder.schema.json
```

These sit above the context object graph schemas:

```text
_repos/shared-backend-components/schemas/context-object.schema.json
_repos/shared-backend-components/schemas/context-version.schema.json
_repos/shared-backend-components/schemas/context-artifact.schema.json
_repos/shared-backend-components/schemas/context-relationship.schema.json
_repos/shared-backend-components/schemas/context-event.schema.json
_repos/shared-backend-components/schemas/context-pack.schema.json
```

## Standards Mapping

| Need | Standard or protocol |
| --- | --- |
| Agent access | MCP |
| Agent collaboration | A2A |
| Linked data | JSON-LD and schema.org |
| Provenance | W3C PROV / PROV-O |
| Pipeline lineage | OpenLineage |
| Runtime traces | OpenTelemetry |
| Dataset catalogs | DCAT |
| Taxonomies | SKOS |
| Identity | OIDC / OAuth |
| Fine-grained authorization | OpenFGA/Zanzibar-style relationship authorization |
| Policy evaluation | OPA/Rego or Cedar |
| Healthcare | FHIR |
| Cyber threat intelligence | STIX/TAXII |
| Software supply chain | SPDX and CycloneDX |
| Supply chain traceability | GS1 EPCIS |
| Industrial systems | OPC UA |
| Built environment | IFC |
| Financial messages and reporting | ISO 20022 and XBRL/iXBRL |

## Packaging

### Developer Context Kit

For Claude Code, Cursor, Rovo Dev, and local agents:

- local Markdown/Obsidian memory;
- repo context-as-code;
- generated repo wiki imports;
- Claude Code skills, hooks, and commands;
- `context_for_ticket`, `context_for_mr`, and `context_for_repo`;
- source-handle conventions;
- local cache manifest.

### Enterprise Context Gateway

For platform and security teams:

- SSO/OIDC;
- MCP gateway or portal integration;
- tool allowlists;
- source allowlists;
- DLP;
- audit logs;
- model routing;
- read/write separation;
- policy checks.

### Context Object Store

For durable context infrastructure:

- object registry;
- versions;
- artifacts;
- relationship graph;
- lineage event log;
- retrieval projections;
- pack builder;
- eval and feedback records.

### Industry Context Packs

Vertical templates:

- software engineering;
- security/SBOM;
- healthcare/FHIR;
- financial services;
- legal/compliance;
- manufacturing/OPC UA;
- supply chain/EPCIS;
- AEC/IFC.

## MVP Roadmap

### First 30 days: Context Pack MVP

- `context_for_ticket`
- `context_for_mr`
- `context_fetch`
- `context_trace`
- Rovo/Jira/Confluence and GitLab/GitHub source adapters
- local Markdown/Obsidian import
- generated repo wiki import
- source-linked packs with retrieval trace

### Days 31-60: Object Registry and Gateway

- context object registry
- version records
- artifact records
- relationship records
- event records
- MCP gateway integration
- basic OIDC/policy checks
- admin browse surface

### Days 61-90: Retrieval and Evals

- hybrid retrieval over one corpus
- graph expansion
- reranking
- source precedence
- conflict detection
- eval cases
- feedback capture
- stale-source checks

## Product Invariants

- The product is not a raw source mirror.
- The product is not only vector search.
- The product is not only a chatbot UI.
- Every durable claim keeps source handles.
- Every derived artifact keeps lineage.
- Every context pack is tied to retrieval, policy, and compression events.
- Raw source expansion is exact-handle-only or fallback by policy.
- Local memory can propose context, but enterprise promotion requires review.
- Generated repo wikis are useful derived artifacts, not source truth.
