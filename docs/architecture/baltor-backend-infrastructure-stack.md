# Baltor Backend Infrastructure Stack

Date: 2026-06-03

Baltor should treat tools like Synapse as one slice of a larger backend
infrastructure stack. Baltor should not become a generic agent-orchestration
product. Its core is the verified context object, source handle, context pack,
lineage, source precedence, policy, and delivery contract.

The right framing is:

```text
Synapse-like tools run Context Wizards.
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
| Worker orchestration / Context Wizard execution | Prototype and run multi-step context workers. | Synapse AI, LangGraph, CrewAI, Mastra |
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
| Context Wizard lab | Synapse AI, LangGraph, CrewAI, Mastra | Fast experimentation with multi-agent or multi-step context workflows. |
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

## Orchestration Tools

### Synapse AI

Synapse-like tools are relevant as a Context Wizard orchestration lab. They can
run:

```text
Source watcher
Reconciler
Fragility hunter
Adversarial interrogator
Context enhancer
Pack compressor
```

Use Synapse for visual workflow prototyping, scheduled context drift checks,
human review workflows, and pack-generation experiments.

Watchouts:

```text
license constraints
enterprise auth / RBAC maturity
workflow versioning
multi-tenant isolation
audit-log depth
durability guarantees
```

### LangGraph

LangGraph is a strong code-first candidate for complex Context Wizard flows. It
fits workers that need explicit state, graph control flow, human-in-the-loop
review, and tracing through LangSmith.

Good Baltor workflows:

```text
claim_extractor_graph
verification_graph
context_pack_builder_graph
human_review_graph
context_refresh_graph
```

### CrewAI

CrewAI is useful for role-based worker prototypes:

```text
Reconciler
Verifier
Enhancer
Compressor
Steward reviewer
```

It is good for conceptual worker teams, but Baltor still needs deterministic
context-object storage and source-handle discipline outside the crew runtime.

### Mastra

Mastra is worth testing if Baltor's backend, SDK, or developer-facing gateway is
TypeScript-heavy. It can support TypeScript-first Context Gateway prototypes,
local developer tooling, and workflow APIs around `context_for_ticket()`.

### Pydantic AI

Pydantic AI is especially relevant because Baltor needs typed, validated outputs:

```text
structured claim extraction
JSON-schema-validated context packs
typed policy decisions
typed verification results
model-output validation
```

It should be paired with a durable workflow system such as Temporal, DBOS,
Prefect, or Restate when workflows must survive failures.

### Microsoft Agent Framework, Google ADK, And OpenAI Agents SDK

These are provider-specific or enterprise-specific implementation options. Use
them for customer-aligned deployment tracks, not as the core Baltor contract.

Best roles:

```text
Microsoft Agent Framework -> Microsoft / Azure / Entra / Graph-heavy buyers
Google ADK -> Google Cloud / Gemini Enterprise buyers
OpenAI Agents SDK -> OpenAI-first worker prototypes and guardrail experiments
```

Important caveat: provider agent SDKs are not sufficient durable workflow
platforms by themselves. They need a reliability layer for checkpointing,
retries, state persistence, and long-running jobs.

### LlamaIndex Workflows, Haystack, AG2 / AutoGen

Use these for research, RAG-heavy pipelines, document-centric workers, and
multi-agent experiments. They can help build prototypes, but should not become
the context authority.

## Durable Workflow Engines

Context Wizards continuously respond to source events, refresh stale claims,
build packs, and wait for human review. That is a durable distributed-systems
problem.

### Temporal

Temporal is the strongest general-purpose durable execution candidate. It is a
good fit for:

```text
source refresh jobs
verification runs
pack builder workflows
memory promotion workflows
human review gates
long-running context drift monitors
```

It provides the right production primitives: crash recovery, retries, workflow
history, schedules, signals, queries, and customer-visible resumability.

### Dapr Agents

Dapr Agents is a strong option when Baltor wants Kubernetes-native durable,
stateful, event-driven workers. It fits actor-like source watchers,
multi-agent verification, and distributed Context Wizard execution.

### Restate, Inngest, Hatchet, And DBOS

These are lighter-weight or startup-friendly durable execution candidates.

| Tool | Baltor role |
|---|---|
| Restate | Lightweight durable execution for `verify_claim()`, `context_for_ticket()`, `refresh_pack()`, and source-handle validation. |
| Inngest | Event-driven backend for source webhooks, scheduled refresh, pack regeneration, and ACL-change handling. |
| Hatchet | Pragmatic orchestration for background Context Wizard queues, agent tasks, and human-in-the-loop eventing. |
| DBOS | Postgres-centered durable workflows and queues, attractive if the early system already uses Postgres heavily. |

### Prefect And Dagster

Use Prefect and Dagster for data-pipeline style work:

```text
batch ingestion
embedding jobs
document parsing
repo wiki regeneration
RAG / index rebuilds
eval dataset generation
```

They are useful for ingestion and batch processing, not necessarily for
interactive Context Wizard runtime.

### Cloudflare Workflows And Agents

Cloudflare is relevant for a Cloudflare-first deployment track:

```text
edge-hosted local/team context gateway
MCP server hosting
lightweight context refresh workflows
AI Gateway logging and rate limits
AI Search / Vectorize experiments
```

## Visual Builders And Low-Code Platforms

Dify, Flowise, Langflow, and n8n are useful for demos, customer-specific
workflows, and internal operations. They should not become Baltor's core
backend.

| Tool | Good Baltor role | Not core because |
|---|---|---|
| Dify | Prototype apps around Baltor context APIs. | It should not be the Verified Context Registry. |
| Flowise | Visual Context Wizard demos and internal POCs. | Visual flow state should not define product state. |
| Langflow | Flow-as-MCP experiments and client demos. | Baltor still owns source handles and policy. |
| n8n | Notify Slack, open Jira, route review, trigger pack refresh. | Business automation is not context authority. |

## MCP Gateway And Tool-Control Infrastructure

Baltor should integrate with this layer rather than rebuilding a full generic
gateway first.

| Gateway | Baltor role |
|---|---|
| Cloudflare MCP Server Portals | Put Baltor MCP behind Cloudflare Access; expose only context tools such as `context_for_ticket`, `context_for_mr`, `context_fetch`, and `context_trace`. |
| IBM Context Forge | Self-hosted enterprise MCP gateway for regulated deployments and multi-protocol federation. |
| Portkey MCP Gateway | Managed or self-hostable MCP control plane with authentication, access control, request logging, and AI gateway integration. |
| TrueFoundry MCP Gateway | Enterprise/private-cloud MCP gateway candidate for VPC or customer-cloud deployments. |

Generic MCP gateways answer:

```text
Can this tool be exposed?
```

Baltor answers:

```text
Which verified, source-linked, fresh, policy-allowed context should this tool return?
```

## Tool Auth And Integration Infrastructure

Baltor does not need to build every SaaS connector action from scratch.

| Tool | Baltor role |
|---|---|
| Arcade | Agent/tool authorization for OAuth, API keys, user tokens, and approval-aware actions. |
| Composio | Broad connector/action provider; useful after Baltor verifies context. |
| Pipedream MCP | Fast app/API integration substrate for Slack, Jira, CRM, and workflow automations. |
| Nango | OAuth, token refresh, permissions, rate limits, logging, and credential handling for production connectors. |

Tool auth infrastructure can perform actions, but Baltor should decide which
context justified the action.

## Graph, Memory, And Retrieval Infrastructure

These providers are useful for the CodeGraph / DocGraph / OrgGraph model.

| Tool | Baltor role |
|---|---|
| Zep / Graphiti | Temporal claim graph and memory backend candidate for changing facts, stale claim invalidation, and relationship-aware context. |
| Cognee | Memory/control-plane experiment for local/team graph memory and document-to-graph experiments. |
| HelixDB | Candidate graph-vector backend for combined CodeGraph, DocGraph, and OrgGraph prototypes. |
| Qdrant | Vector/hybrid retrieval backend for source candidates, metadata filtering, and semantic/exact retrieval. |

The backend can retrieve candidates, but Baltor still needs:

```text
source handles
claim verification
policy filtering
source precedence
context-pack assembly
context receipts
```

## Observability, Tracing, And Evals

Baltor should integrate with existing LLM observability platforms while adding
context-specific metrics.

| Tool | Baltor role |
|---|---|
| LangSmith | Trace Context Wizard runs and downstream consumption. |
| Langfuse | Self-hostable observability for regulated deployments. |
| Arize Phoenix | RAG and context-pack evaluation lab. |
| Braintrust | Pack-quality evals, source recall evals, regression tests, and human annotation workflows. |

Baltor-specific evals should include:

```text
source recall
claim citation coverage
token budget
stale/conflict detection
ACL correctness
raw expansion rate
task success
context-pack usefulness
```

## Secure Sandbox Execution

Some Context Wizards need to parse repos, run tests, inspect code, execute
scripts, or process untrusted source artifacts.

| Tool | Baltor role |
|---|---|
| E2B | Sandboxed code analysis, repo parsing, test execution, document transformation, and untrusted tool execution. |
| Daytona | Developer/repo analysis sandboxes and agent workspace execution. |
| Modal Sandboxes | High-scale source-processing workers, large eval runs, and batch code analysis. |
| Firecracker | Self-hosted regulated microVM substrate. |

Sandbox workers must remain subordinate to Baltor policy. They can inspect and
execute, but they do not promote facts without source-handle and verification
rules.

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

Context Wizards
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
  Context Wizard prototyping

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
