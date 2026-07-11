# Baltor Backend Infrastructure Stack

Date: 2026-06-03

Baltor should treat tools like Synapse as one slice of a larger backend
infrastructure stack. Baltor should not become a generic agent-orchestration
product. Its core is the verified context object, source handle, context pack,
lineage, source precedence, policy, and delivery contract.

The right framing is:

```text
Synapse-like tools run context workers.
Durable workflow engines make those workers reliable.
MCP gateways govern tool access.
Graph/vector stores hold context state.
Eval/observability tools measure quality.
Baltor owns the verified context contract.
```

For the implementation-oriented repo, tool, process, and technology map, see
[Baltor Backend Tooling Research Map](baltor-backend-tooling-research-map.md).

## Product Boundary

Baltor owns:

```text
ContextObject
ContextClaim
SourceHandle
ContextRelationship
ContextPack
ContextReceipt
PolicyDecision
VerificationRun
source precedence
freshness / TTL
context-pack schemas
lineage and audit
policy-aware delivery
```

External infrastructure can help run, store, route, observe, or sandbox the
work, but it should not define Baltor's product model. The external tools are
replaceable providers below the Baltor contract.

## Nine Infrastructure Layers

| Layer | Purpose | Example tools |
|---|---|---|
| Worker orchestration / context worker execution | Prototype and run multi-step context workers. | Synapse AI, LangGraph, CrewAI, Mastra |
| Durable workflow runtime | Make refresh, verification, pack-building, and human-review jobs recoverable. | Temporal, Dapr Agents, Restate, Inngest, Hatchet, DBOS |
| Agent framework / model-calling layer | Typed model calls, handoffs, guardrails, and provider-specific agent patterns. | Pydantic AI, Microsoft Agent Framework, Google ADK, OpenAI Agents SDK |
| MCP gateway and tool control plane | Govern which tools are exposed, logged, and policy-controlled. | Cloudflare MCP Server Portals, IBM Context Forge, Portkey MCP Gateway, TrueFoundry MCP Gateway |
| Tool auth and integration layer | OAuth, delegated credentials, SaaS connectors, and approved actions. | Arcade, Composio, Pipedream, Nango |
| Context object / graph / memory store | Store claims, relationships, temporal memory, and graph/vector state. | Postgres, Zep/Graphiti, Cognee, HelixDB, Qdrant |
| Retrieval and indexing layer | Candidate retrieval, hybrid search, reranking inputs, and metadata filtering. | Qdrant, pgvector, OpenSearch, graph stores |
| Evals, observability, and tracing | Measure context quality, worker behavior, drift, cost, latency, and failures. | LangSmith, Langfuse, Arize Phoenix, Braintrust |
| Secure sandbox execution | Safely parse repos, run tests, execute code, and inspect untrusted artifacts. | E2B, Daytona, Modal Sandboxes, Firecracker |

## Shortlist To Evaluate First

| Layer | First tools to test | Why |
|---|---|---|
| Context worker lab | Synapse AI, LangGraph, CrewAI, Mastra | Fast experimentation with multi-agent or multi-step context workflows. |
| Production durable workers | Temporal, Dapr Agents, Restate, Inngest, Hatchet, DBOS | Long-running verification, refresh, drift, and pack-building jobs need retries, state, and audit. |
| Structured agent code | Pydantic AI, Microsoft Agent Framework, Google ADK, OpenAI Agents SDK | Useful for typed outputs, handoffs, human review, and provider-specific integration paths. |
| MCP gateway | Cloudflare MCP Server Portals, IBM Context Forge, Portkey MCP Gateway, TrueFoundry MCP Gateway | Baltor should sit behind or beside a governed MCP access layer. |
| Tool auth / actions | Arcade, Composio, Pipedream, Nango | Useful for source/action connectors without rebuilding OAuth plumbing first. |
| Graph / memory | Zep/Graphiti, Cognee, HelixDB, Qdrant | Useful for temporal context, graph/vector retrieval, memory, and source relationship modeling. |
| Evals / observability | LangSmith, Langfuse, Arize Phoenix, Braintrust | Needed to measure context-pack quality, drift, source recall, and consumer behavior. |
| Sandbox execution | E2B, Daytona, Modal Sandboxes, Firecracker | Needed for safe code execution, source parsing, repo analysis, and untrusted worker tasks. |

## Recommended Near-Term Stack

Prototype:

```text
Synapse AI or LangGraph
+ FastMCP or TypeScript MCP server
+ Postgres
+ Qdrant or Graphiti
+ Langfuse or Phoenix
```

Production direction:

```text
Temporal or Dapr Agents for worker durability
+ Cloudflare / Portkey / Context Forge MCP gateway
+ Postgres context registry
+ graph/vector backend
+ Braintrust / LangSmith / Langfuse / Phoenix evals
+ E2B / Daytona / Modal for sandboxed code and source analysis
```

## Per-tool detail lives in the tooling map

The per-tool catalog for every layer above — orchestration frameworks, durable workflow engines, visual
builders, MCP gateways, tool-auth connectors, graph/memory/retrieval backends, observability/eval platforms,
and sandbox runtimes — lives in the companion
[Baltor Backend Tooling Research Map](baltor-backend-tooling-research-map.md) (20 sections + reference links).
This document keeps only the strategic framing (layers, shortlist, near-term stack, MVP/production
architecture, ranking) plus the nuances below that the map does not carry.

### Strategic nuances not to lose

- **Synapse-style orchestration labs** run the worker set (Source watcher, Reconciler, Fragility hunter,
  Adversarial interrogator, Context enhancer, Pack compressor) for visual prototyping, scheduled drift checks,
  human-review workflows, and pack-generation experiments. Watchouts before production: license constraints,
  enterprise auth/RBAC maturity, workflow versioning, multi-tenant isolation, audit-log depth, and durability
  guarantees.
- **LangGraph** is the code-first option for stateful worker flows (`claim_extractor_graph`,
  `verification_graph`, `context_pack_builder_graph`, `human_review_graph`, `context_refresh_graph`). CrewAI
  suits role-based worker prototypes (Reconciler, Verifier, Enhancer, Compressor, Steward reviewer); Mastra
  suits TypeScript-first Context Gateway prototypes around `context_for_ticket()`.
- **Provider agent SDKs are not durable workflow platforms** — they need a reliability layer for
  checkpointing, retries, state persistence, and long-running jobs. Best-fit deployment tracks: Microsoft
  Agent Framework -> Microsoft/Azure/Entra/Graph-heavy buyers; Google ADK -> Google Cloud / Gemini Enterprise
  buyers; OpenAI Agents SDK -> OpenAI-first worker prototypes and guardrail experiments. LlamaIndex Workflows,
  Haystack, and AG2/AutoGen suit research, RAG-heavy pipelines, and document-centric workers, but never the
  context authority.
- **Dapr Agents** is the strong option for Kubernetes-native durable, stateful, event-driven workers
  (actor-like source watchers, multi-agent verification, distributed worker execution). Temporal remains the
  strongest general-purpose durable engine (crash recovery, retries, workflow history, schedules, signals,
  queries, resumability); Restate/Inngest/Hatchet/DBOS are lighter-weight starts; Prefect/Dagster fit
  data-pipeline batch work; Cloudflare Workflows fit a Cloudflare-first edge track.
- **Visual builders** (Dify, Flowise, Langflow, n8n) are for demos, customer-specific workflows, and internal
  operations — not the core backend: Dify should not be the Verified Context Registry; Flowise/Langflow visual
  flow state should not define product state; n8n business automation is not context authority.
- **Tool-auth connectors** (Arcade, Composio, Pipedream, Nango) perform actions, but Baltor decides which
  context justified the action. Arcade adds approval-aware OAuth/token authorization; Composio is a broad
  connector/action provider; Pipedream is a fast Slack/Jira/CRM integration substrate; Nango handles OAuth,
  token refresh, permissions, rate limits, and logging for production connectors.
- **The MCP-gateway distinction is the boundary:** a generic MCP gateway answers *"Can this tool be
  exposed?"*; Baltor answers *"Which verified, source-linked, fresh, policy-allowed context should this tool
  return?"* Expose only context tools (`context_for_ticket`, `context_for_mr`, `context_fetch`,
  `context_trace`); hide raw source tools. Candidate gateways: Cloudflare MCP Server Portals, IBM Context
  Forge, Portkey MCP Gateway, TrueFoundry MCP Gateway.
- **Graph/retrieval and sandbox backends stay subordinate to Baltor.** Graph/memory (Zep/Graphiti, Cognee,
  HelixDB, Qdrant) retrieve candidates, and sandboxes (E2B, Daytona, Modal, Firecracker) inspect/execute code,
  but neither promotes facts without source handles, claim verification, policy filtering, source precedence,
  pack assembly, and receipts. Observability/evals (LangSmith, Langfuse, Arize Phoenix, Braintrust) must add
  Baltor-specific metrics: source recall, claim citation coverage, token budget, stale/conflict detection, ACL
  correctness, raw-expansion rate, and task success.

## MVP Architecture

```text
Baltor API / MCP
  FastMCP or TypeScript MCP SDK

Worker lab
  Synapse AI or LangGraph

Durability
  Inngest / Hatchet / DBOS for quick start
  or Temporal if enterprise durability is required immediately

Context registry
  Postgres

Retrieval
  Qdrant for hybrid candidate retrieval

Graph / memory
  Graphiti or Cognee experiment

Observability
  Langfuse or Phoenix

Sandbox
  E2B or Daytona
```

MVP product surface:

```text
context_for_ticket()
context_for_mr()
verify_claim()
context_fetch()
context_trace()
```

## Production Architecture

```text
Baltor Context Gateway
  REST + MCP + GraphQL
  AuthN/AuthZ
  policy decisions
  source-handle expansion

Context Object Fabric
  Postgres for canonical records
  graph store for relationships
  vector/hybrid search for candidates
  object store for artifacts
  event log for source changes

Worker Orchestration
  Temporal or Dapr Agents
  Synapse / Flowise / Langflow only for experiments and demos

Context workers
  Source watcher
  Reconciler
  Fragility hunter
  Interrogator
  Enhancer
  Compressor
  Steward review router

Tool / Gateway Layer
  Cloudflare MCP Portal or Context Forge / Portkey / TrueFoundry
  Nango / Arcade / Pipedream / Composio for auth and actions

Evals / Observability
  Langfuse / LangSmith / Phoenix / Braintrust

Sandbox Execution
  E2B / Daytona / Modal / Firecracker
```

## Strategic Ranking

Tier 1, must evaluate:

```text
Temporal
Dapr Agents
LangGraph
Pydantic AI
Cloudflare MCP Portals
IBM Context Forge
Portkey MCP Gateway
Graphiti / Zep
Qdrant
Langfuse
Braintrust
E2B or Daytona
```

Tier 2, useful depending on stack:

```text
Synapse AI
CrewAI
Mastra
Microsoft Agent Framework
Google ADK
LlamaIndex Workflows
Haystack
Restate
Inngest
Hatchet
DBOS
Arize Phoenix
Composio
Arcade
Nango
Pipedream
```

Tier 3, demos or specific customers:

```text
Dify
Flowise
Langflow
n8n
AG2 / AutoGen
Cloudflare Agents / Workflows
Modal Sandboxes
Cognee
HelixDB
```

## Recommendation

Do not choose one "Synapse replacement." Choose one tool per backend role.

Recommended starting set:

```text
LangGraph or Synapse AI:
  Context worker prototyping

Temporal or Dapr Agents:
  production durable worker engine

Postgres:
  canonical context registry

Qdrant:
  hybrid retrieval backend

Graphiti:
  temporal claim / relationship graph experiment

Cloudflare MCP Portal or IBM Context Forge:
  enterprise MCP gateway

Langfuse + Braintrust:
  observability + evals

E2B or Daytona:
  sandboxed code/source execution
```

The strategic distinction should remain:

```text
Orchestration tools decide how workers run.
Baltor decides what context is verified, source-linked, fresh, allowed,
compressed, and safe to serve.
```

That keeps Baltor out of the crowded "agent workflow builder" market while
still using that ecosystem as backend infrastructure.

## Reference Links

- Synapse AI Docs: <https://docs.synapseorch.com/>
- LangGraph: <https://docs.langchain.com/oss/python/langgraph/overview>
- CrewAI: <https://docs.crewai.com/en/introduction>
- Mastra: <https://mastra.ai/>
- Pydantic AI: <https://pydantic.dev/docs/ai/overview/>
- Microsoft Agent Framework: <https://learn.microsoft.com/en-us/agent-framework/overview/>
- Google ADK: <https://adk.dev/>
- OpenAI Agents SDK: <https://developers.openai.com/api/docs/guides/agents>
- Temporal: <https://temporal.io/>
- Dapr Agents: <https://docs.dapr.io/developing-ai/dapr-agents/>
- Restate AI agents: <https://docs.restate.dev/use-cases/ai-agents>
- Inngest: <https://www.inngest.com/>
- Hatchet: <https://hatchet.run/>
- DBOS: <https://www.dbos.dev/>
- Cloudflare Agents: <https://developers.cloudflare.com/agents/>
- Cloudflare MCP Server Portals: <https://developers.cloudflare.com/cloudflare-one/access-controls/ai-controls/mcp-portals/>
- IBM Context Forge: <https://github.com/IBM/mcp-context-forge>
- Portkey MCP Gateway: <https://docs.portkey.ai/docs/product/mcp-gateway>
- TrueFoundry MCP Gateway: <https://www.truefoundry.com/docs/ai-gateway/mcp/mcp-overview>
- Arcade: <https://docs.arcade.dev/home/auth/how-arcade-helps>
- Composio toolkits: <https://composio.dev/toolkits>
- Pipedream MCP: <https://pipedream.com/docs/connect/mcp>
- Nango tool calling: <https://nango.dev/docs/getting-started/use-cases/tool-calling>
- Graphiti: <https://github.com/getzep/graphiti>
- Cognee: <https://www.cognee.ai/>
- HelixDB: <https://github.com/helixdb/helix-db>
- Qdrant hybrid queries: <https://qdrant.tech/documentation/search/hybrid-queries/>
- LangSmith observability: <https://www.langchain.com/langsmith/observability>
- Langfuse docs: <https://langfuse.com/docs>
- Arize Phoenix: <https://github.com/arize-ai/phoenix>
- Braintrust: <https://www.braintrust.dev/>
- E2B docs: <https://e2b.dev/docs>
- Daytona: <https://www.daytona.io/>
- Modal Sandboxes: <https://modal.com/products/sandboxes>
- Firecracker: <https://github.com/firecracker-microvm/firecracker>
