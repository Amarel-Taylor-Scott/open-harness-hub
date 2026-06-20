# Baltor Complete System Brief

Baltor is a governed context fabric for AI-assisted work.

It turns scattered organizational knowledge from files, code, tickets, docs,
messages, runbooks, generated repo wikis, local memory, and source systems into
versioned, permission-aware, source-linked context that humans and AI agents can
use safely.

The complete architecture is intentionally broad, but the first product wedge is
narrower: trusted context packs for AI-assisted engineering. See
`docs/architecture/baltor-product-market-fit-and-wedge-strategy.md` for the product-market-fit strategy,
initial ICP, MVP scope, validation plan, and what to de-emphasize before paid
demand is proven.

Baltor is not just RAG, not just memory, not just an MCP gateway, and not just a
chatbot over documents. It is a context supply chain.

```text
raw sources
  -> normalized context objects
  -> versions, artifacts, claims, dimensions, relationships
  -> retrieval, reranking, model routing, compression
  -> task-specific context packs
  -> MCP/API/local tools for agents and humans
```

The core promise:

```text
Any agent can ask for context.
Baltor returns the smallest safe, source-linked, policy-compliant context pack
needed for the task, with evidence, relationships, history, and lineage intact.
```

## The Problem

AI assistants are only as good as the context they receive. In real companies,
that context is fragmented:

```text
Jira issues
Confluence pages
GitLab/GitHub repos
merge requests
CI/CD artifacts
Slack/Teams conversations
incident reports
runbooks
generated repo wikis
local developer notes
customer/support records
security findings
data catalogs
regulated records
```

The common failure modes are:

```text
agents read too much raw source
agents miss important related sources
agents use stale or superseded facts
agents ignore source permissions
agents treat comments as decisions
agents cannot explain where context came from
teams cannot audit what an agent saw
local memory becomes uncontrolled
central RAG treats everything like a document blob
encrypted private memory cannot be searched centrally
```

Enterprises do not need another generic chatbot over company docs. They need
governed context infrastructure.

## Product-Market Fit

Baltor should prove product-market fit through the narrow engineering-agent wedge first, not by
selling the entire context fabric on day one.

Launch positioning:

```text
Baltor gives AI coding agents trusted context packs for every ticket and pull
request: source-linked, permission-aware, fresh, and auditable.
```

The broader product can grow after this wedge proves paid demand.

Baltor fits organizations adopting Claude Code, ChatGPT, Cursor, Rovo Dev,
internal agents, CI agents, or support/security copilots where context quality
now limits adoption.

The best early market is engineering and platform teams because they have:

```text
ticket-driven work
large codebases
high context-switching cost
clear source systems
clear proof tasks
measurable time savings
security concerns around MCP/tools
```

The strongest initial use cases:

```text
context_for_ticket()
context_for_mr()
context_for_repo()
review_pack()
debugging_pack()
incident_pack()
local encrypted developer memory
repo wiki import and compression
source-handle cache
MCP gateway controls
```

Later markets include:

```text
security operations
support/customer success
legal/compliance
healthcare
financial services
manufacturing
supply chain
construction/AEC
data/analytics
```

## Value

Baltor creates value by making AI context:

```text
safer
smaller
fresher
source-linked
permission-aware
versioned
auditable
relationship-rich
offline-capable where appropriate
cloud-governed where necessary
```

For developers:

```text
less repeated repo spelunking
faster ticket implementation
better MR review context
offline local memory
clear source handles
fewer stale assumptions
```

For platform teams:

```text
one approved agent context contract
MCP/API governance
tool and source boundaries
standard context-pack format
portable provider-neutral model routing
observable retrieval and compression
```

For security/compliance:

```text
ACL-before-model enforcement
raw source expansion controls
audit trails
lineage
prompt-injection risk handling
encrypted local memory boundaries
separation of private memory and company-readable context
```

For executives:

```text
accelerated AI adoption
reduced hallucination risk
better reuse of institutional knowledge
measurable developer productivity
governed path from local pilots to enterprise rollout
```

## Core Architecture

```text
Claude Code / ChatGPT / Cursor / Rovo Dev / CI agents / internal apps
  -> MCP, REST, GraphQL, A2A, webhooks, SDKs
  -> Baltor Context Gateway
  -> Context Object Fabric
  -> providers, indexes, local memory, generated artifacts, source systems
```

The system has six main layers.

```text
1. Source layer
   Jira, Confluence, GitLab, GitHub, Obsidian, repo wikis, Slack, CI,
   observability, support, security, data, and industry systems.

2. Object layer
   Context objects, versions, artifacts, claims, assertions, dimensions,
   relationships, packs, policies, and lineage.

3. Retrieval layer
   Exact handle fetch, keyword/BM25, vector, hybrid search, graph traversal,
   temporal retrieval, source precedence, and policy filtering.

4. Reranking and compression layer
   Deterministic filters, lexical/vector ranking, cross-encoder reranking,
   LoRA/domain rerankers, LLM judges, source-aware context-pack building.

5. Control layer
   Identity, ACLs, policy, DLP, audit, retention, evals, feedback, model
   routing, queue health, worker orchestration, and MCP controls.

6. Delivery layer
   MCP tools/resources, REST APIs, local MCP, CLI, UI, CI hooks, and context
   packs for agents.
```

## Context Object Model

Baltor models knowledge as flexible, versioned, permissioned context objects.

```text
ContextObject:
  stable identity + flexible facets

ContextVersion:
  immutable historical state

ContextRelationship:
  unlimited typed edges and hyperedges

ContextAssertion:
  source-linked facts and claims

ContextDimension:
  extensible numeric/categorical scoring

ContextArtifact:
  derived chunks, summaries, embeddings, repo wikis, packs

ContextLineage:
  proof of where everything came from

ContextPolicy:
  who can see, use, expand, store, or export it

ContextPack:
  task-specific compressed delivery format
```

The object envelope stays small and stable. Long-tail attributes live in
namespaced facets:

```text
core.*
jira.*
confluence.*
gitlab.*
github.*
rovo.*
deepwiki.*
obsidian.*
engineering.*
security.*
healthcare.fhir.*
finance.iso20022.*
legal.*
supplychain.epcis.*
custom.<team>.*
```

Relationships and scores do not bloat the object document. They are first-class
records attached to objects.

## Dimensions

Baltor supports 5W1H and custom scoring dimensions.

```text
who
what
when
where
why
how
```

Built-in scoring dimensions include:

```text
authority
verifiability
freshness
human verification
conflict level
operational risk
security risk
compliance risk
business impact
sensitivity
actionability
completeness
specificity
stability
traceability
prompt-injection risk
token efficiency
```

Scores are assessments, not source facts. They carry scope, method, confidence,
evidence, validity windows, and lineage.

## Relationships

Baltor supports unlimited relationships.

Common relationship types:

```text
contains
part_of
references
mentions
explains
contradicts
confirms
supersedes
implements
implemented_by
changes
defines
calls
tests
owned_by
approved_by
governed_by
derived_from
generated_by
used_as_input_to
affected_by
failed_due_to
recovered_by
```

Some relationships are n-ary, not simple edges:

```text
Alice approved ADR-014 for billing-service during architecture review
```

That becomes a relationship object with endpoints:

```text
approver
approved_object
applies_to
approval_event
time
evidence
```

## Source Handles

Every durable claim needs expandable source handles.

Examples:

```text
ctx://acme/jira/issue/BILL-782#acceptance-criteria
ctx://acme/confluence/page/ADR-014#retry-policy
ctx://acme/gitlab/project/17/mr/4421
ctx://acme/repo/billing-service/file/services/billing/retry_scheduler.ts
ctx://acme/context-pack/BILL-782/implementation/latest
```

Source handles let the agent consume compact context first and expand only when
needed.

## Context Packs

Context packs are the primary delivery artifact.

Common pack types:

```text
implementation_pack
review_pack
debugging_pack
architecture_pack
ticket_pack
incident_pack
release_pack
support_pack
security_triage_pack
compliance_pack
clinical_summary_pack
legal_matter_pack
financial_risk_pack
```

An implementation pack includes:

```text
summary
requirements
decisions
code pointers
risks
conflicts
tests to run
source handles
freshness
lineage
policy decision
```

The agent should receive the smallest sufficient pack, not raw source dumps.

## Local Encrypted Memory

Baltor uses a split-brain memory design.

```text
Private local memory:
  works offline
  encrypted locally or E2EE synced
  locally searchable
  cloud cannot normally search it

Company context:
  centrally governed
  permission-aware
  searchable by approved company services
  encrypted at rest, but company context service can read/index it
```

Important rule:

```text
If the cloud cannot decrypt private memory, the cloud cannot normally build
server-side embeddings, semantic search, reranking, summarization, or token
compression over it.
```

Memory classes:

```text
private_local
team_encrypted
repo_encrypted
org_approved_cache
company_context
```

Offline behavior:

```text
read local memory
write local memory
search local index
use cached company context packs
label freshness as last-validated
queue encrypted sync events
disable source-system writes
```

Online behavior:

```text
sync encrypted memory events
query company context gateway
refresh cached packs
validate source handles
flag stale local claims
```

## Cloud Capabilities

Baltor cloud can provide:

```text
company context gateway
MCP portal/gateway integration
connector management
source sync orchestration
permission-aware indexes
context object registry
relationship graph
artifact store
context-pack builder
reranking and model routing policy
central audit logs
queue/workflow monitoring
evals and feedback
encrypted private-memory relay
device sync cursors
team/repo/org key scopes
```

Cloud should not pretend private E2EE memory is centrally searchable. It can
store encrypted blobs, encrypted events, attachments, sync cursors, and metadata.
Search happens locally unless the memory is promoted into a company-readable
context tier.

## Connectors

Connector classes:

```text
Atlassian:
  Jira, Confluence, Rovo, Teamwork Graph

Code:
  GitLab, GitHub, Bitbucket, Sourcegraph, repo wiki tools

Local:
  Obsidian, Markdown, CLAUDE.md, AGENTS.md, local context cache

Enterprise knowledge:
  SharePoint, Google Drive, Notion, Slack, Teams, Glean, Onyx

Engineering:
  CI/CD, Sentry, Datadog, Grafana, Splunk, feature flags, incidents

Business:
  Salesforce, Zendesk, Intercom, CRM, support, contracts, BI

Industry:
  FHIR, STIX/TAXII, CycloneDX/SPDX, EPCIS, OPC UA, IFC, ISO 20022, XBRL
```

Connector modes:

```text
federated
mirrored
indexed
compiled
link-only
action-capable
```

Phase 1 should keep source systems read-only or ask-before-write.

## Repo Wiki and DeepWiki-Style Artifacts

DeepWiki-style tools are repo context artifact providers.

```text
repo
  -> generated wiki / architecture docs / diagrams
  -> repo_wiki_page context artifacts
  -> linked to commits, files, symbols, tickets, services
```

Generated repo wikis are useful compressed context, but they are not source of
truth. They should be:

```text
derived artifacts
commit-scoped
source-linked
versioned
rerankable
superseded by current code where conflicts exist
```

## Sync and Triggers

Baltor supports push, pull, and push-then-pull sync.

Trigger examples:

```text
post_commit_hook
push_webhook
merge_request_webhook
pipeline_artifact
file_watcher
scheduled_poll
release_tag
manual_refresh
source_acl_change
```

Check gates:

```text
signature verification
replay window
connector scope
source ACL before model
event filters
artifact manifest schema
content hash
prompt-injection scan
idempotency key
staleness policy
```

Events should produce derived artifacts, not uncontrolled raw source ingestion.

## Reranking

Baltor treats reranking separately from model routing.

```text
model routing:
  which worker/reviewer should handle the task

reranking:
  which retrieved candidates should enter the pack and in what order
```

Reranking ladder:

```text
deterministic filters
  -> lexical rankers
  -> vector/hybrid rankers
  -> cross-encoder rerankers
  -> LoRA/domain rerankers
  -> LLM judge rerankers
  -> human review
```

LoRA rerankers are adapter profiles:

```text
base reranker
  + tenant/domain/task LoRA adapter
  + eval gate
  + lineage
  + source handles
```

They are not global truth. They must be promoted only after evaluation.

## Model Routing

The model ladder is provider-neutral.

```text
deterministic systems
  -> small cheap/local models
  -> mid open-weight models
  -> large open/high-capability models
  -> ensemble review
  -> frontier appeal
  -> human review
```

Model family examples such as MiniMax, Kimi, DeepSeek, GLM, Nemotron, Granite,
Jamba, Llama, Mistral, Gemma, Qwen, and frontier APIs are swappable examples,
not hard-coded strategy.

Routing uses:

```text
task type
cost
latency
privacy
uncertainty
conflict
temporal fragility
ambiguity
graph centrality
downstream risk
source quality
model disagreement
domain sensitivity
```

Do not escalate by brand. Escalate by risk.

## MCP and API Surface

Current gateway concepts:

```text
context_status
context_search
context_fetch
context_trace
context_connectors
context_sync_contracts
context_object_schema
context_schema_catalog
context_product_surface
context_heartbeat
context_queue_health
context_glossary
context_dimensions
context_model_routing
context_reranking
context_local_memory
```

Future local MCP tools:

```text
remember()
search_memory()
context_for_ticket()
context_for_repo()
write_context_pack()
sync_status()
sync_now()
validate_sources_when_online()
```

Core REST endpoints:

```text
/api/context-gateway/status
/api/context-gateway/search
/api/context-gateway/fetch
/api/context-gateway/trace
/api/context-gateway/connectors
/api/context-gateway/sync-contracts
/api/context-gateway/context-object-schema
/api/context-gateway/context-schema-catalog
/api/context-gateway/product-surface
/api/context-gateway/glossary
/api/context-gateway/dimensions
/api/context-gateway/model-routing
/api/context-gateway/reranking
/api/context-gateway/local-memory
```

## Users

Primary users:

```text
developers
staff engineers
engineering managers
platform engineers
AI enablement teams
security engineers
compliance teams
support engineers
data/analytics teams
solution architects
```

Admin users:

```text
source connector admins
MCP gateway admins
policy admins
security reviewers
context stewards
domain owners
repo maintainers
```

Agent users:

```text
Claude Code
ChatGPT
Cursor
Rovo Dev
CI review agents
Slack/Teams agents
support copilots
security triage agents
internal workflow agents
```

## Feature Set

Developer features:

```text
local encrypted memory
offline context cache
context_for_ticket
context_for_mr
context_for_repo
source-handle expansion
repo wiki context
Claude Code MCP integration
memory write approvals
freshness labels
```

Platform features:

```text
context object registry
schema catalog
MCP/API gateway
connectors
sync contracts
worker queues
context-pack builder
model routing
reranking
dimension engine
lineage
auditing
evals
feedback
```

Security features:

```text
ACL-before-model policy
read/write separation
raw source fallback only
prompt-injection scanning
classification and retention
local E2EE memory relay
source handle validation
policy decisions
audit trails
```

Cloud features:

```text
central connector registry
company context index
context graph
artifact store
queue orchestration
device sync relay
encrypted event storage
MCP gateway integration
central observability
eval dashboard
policy center
admin console
```

## Deployment Models

```text
local-first developer
repo context-as-code
Atlassian/Rovo team deployment
enterprise MCP gateway
custom context object platform
regulated enclave
industry network
```

Recommended progression:

```text
1. Markdown/Obsidian memory
2. local-context MCP
3. encrypted sync
4. repo wiki/import artifacts
5. team-distributed Claude Code kit
6. enterprise MCP gateway
7. company context MCP
8. central indexed context backend
9. context graph, evals, industry packs
```

## Standards Mappings

Baltor maps to existing standards instead of inventing everything.

```text
MCP:
  agent tool/resource access

A2A:
  agent-to-agent collaboration

JSON Schema:
  validation

JSON-LD / schema.org:
  linked semantic objects

W3C PROV:
  provenance

W3C Web Annotation:
  evidence selectors

OpenLineage:
  ingestion and pipeline lineage

OpenTelemetry:
  runtime tracing

DCAT / SKOS:
  catalogs and taxonomies

OIDC/OAuth:
  identity

OpenFGA/Zanzibar:
  relationship-based authorization

OPA/Rego or Cedar:
  policy evaluation

FHIR, STIX/TAXII, CycloneDX, SPDX, EPCIS, OPC UA, IFC, ISO 20022, XBRL:
  industry-specific context variants
```

## Business Model

Possible packaging:

```text
Developer Context Kit
  local MCP, memory, repo context, Claude Code kit

Enterprise Context Gateway
  MCP gateway integration, SSO, policy, audit, tool controls

Context Object Store
  registry, versions, relationships, artifacts, packs, lineage

Industry Context Packs
  healthcare, finance, security, legal, manufacturing, supply chain, AEC
```

Pricing surfaces could be:

```text
per developer seat
per indexed source/object volume
per context-pack generation volume
per connector
enterprise gateway tier
regulated enclave tier
industry pack tier
support/professional services
```

The strategic moat is not the vector database. It is the governed context object
contract, source-handle discipline, relationship graph, context-pack assembly,
local-to-cloud memory model, and policy-aware agent delivery.

## Competitive Position

Baltor complements rather than replaces many tools:

```text
Rovo / Teamwork Graph:
  work-context provider

Glean / Onyx / enterprise search:
  search provider

DeepWiki / repo wiki tools:
  generated repo context provider

Obsidian / Markdown:
  local memory provider

Qdrant / Weaviate / Chroma / LanceDB:
  retrieval backend

Cloudflare / Context Forge / Portkey / MCP gateways:
  gateway and control plane
```

Baltor owns:

```text
context object contract
source handles
pack formats
source precedence
lineage
relationships
dimensions
local encrypted memory bridge
reranking and model-routing policy
evals and feedback
agent delivery contract
```

## MVP Roadmap

30 days:

```text
context_for_ticket
context_for_mr
context_search
context_fetch
context_trace
source-linked packs
local Markdown/Obsidian memory
basic Claude Code MCP
```

60 days:

```text
context object registry
versions
relationships
artifacts
dimensions
local encrypted memory profile
connector catalog
MCP gateway integration
```

90 days:

```text
hybrid retrieval
reranking
model routing
eval cases
feedback loop
conflict detection
source precedence
encrypted sync relay prototype
```

Longer term:

```text
central indexed backend
organization gateway
industry packs
regulated enclaves
graph/temporal memory
team memory promotion
domain LoRA rerankers
human review queues
context marketplace
```

## Key Product Invariants

```text
Durable claims require source handles.
Raw source dumps are not memory.
Generated repo wikis are derived artifacts.
Private E2EE memory is not cloud-searchable.
Company context is a separate governed index.
Embeddings are sensitive derived data.
Reranking is source-aware, not embedding-only.
LoRA/domain rerankers require eval and lineage.
Model routing is provider-neutral.
Escalation depends on risk, not brand.
Context packs record retrieval policy and lineage.
Offline cached context requires TTL and freshness labels.
Source-system writes are disabled offline.
Local memory promotion requires review.
```

## Why This Matters

LLMs make context operational. That means context now needs the same discipline
companies already apply to code, data, identity, and security:

```text
versioning
source control
permissions
lineage
policy
auditing
quality checks
runtime observability
cost management
feedback loops
```

Baltor is the system that makes context itself governable.

The practical end state:

```text
Claude Code starts.
It connects to local MCP.
It sees private memory, repo memory, cached packs, and company context.
It asks Baltor for task-specific context.
Baltor returns a compact, source-linked, permission-aware context pack.
The agent works.
Every source, claim, rank, route, expansion, and decision remains traceable.
```

That is the product.
