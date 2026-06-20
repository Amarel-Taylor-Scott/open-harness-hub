# Baltor Adjacent Market Map

Updated: 2026-06-02

This document captures the adjacent product landscape around Baltor. It is a
strategy and review artifact, not operational truth. Vendor facts, funding
status, model support, and product claims should be refreshed before external
publication or sales use.

## Anchor

Baltor is a governed context supply chain for enterprise agents. It turns
fragmented enterprise sources into source-linked, versioned, permission-aware,
task-specific context packs and records what context was served.

The strongest early wedge remains engineering workflow context:

```text
context_for_ticket
context_for_mr
context_for_repo
implementation_pack
review_pack
debugging_pack
incident_pack
architecture_pack
local encrypted developer memory
source-handle cache
MCP/API delivery
```

The competitive lesson is that most adjacent products own one slice of the
context problem. Baltor should become the contract and control plane across
those slices:

```text
source handles
context-pack schemas
source precedence
lineage
local/team/company memory boundaries
policy-aware retrieval
reranking and compression
evals and feedback
agent delivery
```

## Market Categories

| Category | What it owns | Baltor relationship |
| --- | --- | --- |
| Agent memory and context layers | Persistent memory across agents, apps, and conversations. | Adjacent competitor/provider for local and team memory. |
| Codebase context and repo intelligence | Repo maps, generated docs, semantic code search, PR context. | Directly adjacent to engineering packs. |
| Enterprise search and work graphs | Permission-aware broad company search. | Provider, partner, or substitute for broad retrieval. |
| MCP gateways and tool infrastructure | Agent tool access, auth, action governance, deployment. | Complementary gateway layer; Baltor owns context meaning. |
| RAG and retrieval platforms | Ingestion, chunking, embeddings, hybrid retrieval, reranking. | Backend provider; not the strategic surface alone. |
| Graph, vector, and context databases | Relationship-rich storage and vector/graph traversal. | Infrastructure for context objects and relationships. |
| Architecture and service catalogs | Services, owners, dependencies, diagrams, flows, APIs. | High-authority context providers. |
| Data-agent semantic layers | Warehouse, BI, metric, and data-document context. | Domain-specific analog for data teams. |
| Docs generation and docs repair | AI-optimized docs, repo wikis, KB gap detection. | Derived context artifact providers. |
| Agent observability and evals | Traces, tool calls, cost, failures, quality monitoring. | Feedback and evaluation providers. |
| Agent validation and review | PR review, test generation, QA, IaC review. | Context-pack consumers and artifact producers. |
| Local-first encrypted knowledge | Markdown, Obsidian-style vaults, local DB, encrypted sync. | Substrate for private developer memory. |

## Closest Watchlist

High-priority companies and projects to track:

| Name | Segment | Why it matters |
| --- | --- | --- |
| Hyperspell | Agent memory/context layer | Similar “memory and context layer for agents” positioning over workspace data. |
| Nessie | AI conversation memory | Treats AI conversation history as queryable provenance-linked context. |
| Memory Store | Shared agent memory | Team memory layer for agents from work apps. |
| Mem0 | Agent memory API | Generic memory API that may be backend/provider or memory-layer competitor. |
| Zep / Graphiti | Temporal context graph | Strong temporal memory and graph retrieval substrate. |
| Airweave | Open-source context retrieval | Connector/retrieval layer that may sit below Baltor. |
| Driver | Codebase context layer | Directly adjacent to repo maps, architecture maps, and MCP-served code context. |
| Swimm | Agentic codebase context | Validated repo knowledge, architecture maps, dependency maps, and MCP endpoints. |
| Sourcebot | Code understanding/search | Possible code-context provider for large repos. |
| Greptile | Codebase AI / PR review | Adjacent code understanding and review-pack competitor/provider. |
| Nozomio / Nia | MCP code/docs context | Direct local/dev MCP context wedge. |
| Kaelio | Data-agent context layer | Domain-specific analog for data and BI context. |
| Airbyte Context Store | Business entity context | Entity-centric context store over business apps. |
| HelixDB | Graph-vector database | Potential relationship/vector backend. |
| Compresr | Context compression | Relevant to smallest sufficient context pack economics. |
| Manufact / mcp-use | MCP infrastructure | Gateway/deployment partner for MCP servers and apps. |
| Clawvisor | Agent authorization | Task-scoped auth, approvals, risk scoring, and audit layer. |
| HumanLayer | Human approval layer | Useful for high-risk expansion, memory promotion, and write approval. |
| The Context Company | Agent observability | Relevant to context-pack usage, failures, cost, and trace quality. |
| RefineTrain | Docs optimization | AI-optimized docs provider; must preserve original-source lineage. |
| Outlit | Customer context profile | Domain context layer for customer success/support expansion. |

## Engineering Context Threats

The closest developer-context threats are:

```text
Driver
Swimm
Nozomio / Nia
Greptile
Sourcebot
Glean Claude Code plugin
Atlassian Rovo MCP
```

Baltor should not compete as generic repo search. The sharper claim is:

```text
For this ticket or merge request, Baltor assembles the smallest safe,
source-linked implementation or review pack across code, docs, tickets,
architecture, prior changes, local memory, tests, and policy.
```

That is stronger than repo understanding because it spans source systems,
permissions, source precedence, lineage, and task-specific packaging.

## Memory Layer Implications

Memory should be classified context, not a single undifferentiated store:

```text
private_local
team_encrypted
repo_encrypted
org_approved_cache
company_context
```

The durable Baltor workflow is memory promotion:

```text
local/private note
  -> proposed team memory
  -> reviewed repo memory
  -> org-approved context artifact
  -> indexed company context
```

Rules:

```text
Raw source dumps are not memory.
Durable claims require source handles.
Private end-to-end encrypted memory is not centrally searchable.
Company context is a separate governed index.
Generated repo wikis are derived artifacts, not source of truth.
```

## Provider Strategy

Baltor should integrate, not rebuild, most adjacent infrastructure first.

Strong provider categories:

| Provider class | Examples | Baltor use |
| --- | --- | --- |
| Enterprise search | Glean, Onyx, GoSearch, Rovo, Microsoft Graph, Gemini Enterprise | Broad source retrieval and company search. |
| Code context | Sourcebot, Driver, Swimm, Greptile, Nia, Sourcegraph | Repo maps, symbols, PR history, codebase explanations. |
| Architecture/service graph | IcePanel, Backstage, Port, EventCatalog, Structurizr, LikeC4 | Ownership, dependencies, diagrams, services, events, APIs. |
| MCP/auth infrastructure | Manufact, Arcade, Clawvisor, Nango, Pipedream, Composio, Context Forge, TrueFoundry | Tool deployment, auth, gateway policy, action control. |
| Retrieval backend | Qdrant, Weaviate, HelixDB, Chroma, LanceDB, Ragie, LlamaCloud, Vectara | Vector, hybrid, graph, reranking, indexing. |
| Observability/evals | LangSmith, Langfuse, Braintrust, The Context Company, Synth | Agent traces, pack outcomes, retrieval quality, cost. |

## Build Versus Integrate

Build the durable Baltor surface:

```text
source-handle grammar
context-pack schema
context object registry
context version and lineage model
local encrypted memory bridge
context_for_ticket
context_for_mr
context_for_repo
context_fetch
context_trace
source precedence rules
memory promotion workflow
pack lineage and evaluation model
```

Integrate or partner for replaceable infrastructure:

```text
generic MCP gateways
generic OAuth/action connectors
generic vector stores
generic enterprise search UI
generic observability dashboards
generic diagram canvases
generic coding agents
```

## Positioning

One-liner:

```text
Baltor gives AI agents the smallest safe, source-linked context pack needed for
a ticket, merge request, repo, incident, or review, with permissions, freshness,
lineage, and local memory boundaries built in.
```

Contrast:

```text
RAG retrieves chunks.
Baltor delivers governed context packs.

Memory remembers things.
Baltor decides which remembered things are safe, current, source-linked, and
task-relevant.

MCP gateways expose tools.
Baltor defines the context those tools should return.

Search finds documents.
Baltor assembles task-specific, auditable context from documents, code,
tickets, architecture, memory, and live systems.
```

## Immediate Product Implications

Highest-priority integration order:

```text
1. Claude Code / Cursor / ChatGPT MCP delivery
2. Jira + Confluence + GitLab/GitHub source handles
3. IcePanel + Backstage/Port architecture and service graph providers
4. Glean or Onyx as broad search provider
5. Sourcebot/Swimm/Driver-style repo artifacts
6. Clawvisor/Arcade/Manufact for auth and MCP infrastructure
7. Qdrant/HelixDB/Weaviate for graph/vector backend experiments
```

What not to build first:

```text
general diagram editor
generic vector database
generic MCP gateway
generic connector marketplace
general enterprise search UI
generic coding agent
```

## Competitive Takeaway

The market is crowded, but much of it is still slice-based:

```text
memory API
code search/index
enterprise search
RAG backend
MCP gateway
agent auth layer
architecture catalog
observability tool
testing/review agent
```

Baltor’s white space is the governed context governance and packaging layer:

```text
source systems
  -> context objects
  -> source handles
  -> source precedence
  -> local/team/company memory boundaries
  -> task-specific packs
  -> policy-aware MCP/API delivery
  -> evals and traceability
```

The immediate wedge should stay concrete:

```text
Before Claude Code works on this Jira ticket or GitLab merge request, Baltor
gives it the right bounded implementation or review pack, with source handles
and policy decisions.
```
