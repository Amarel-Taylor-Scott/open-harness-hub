# Baltor Backend Tooling Research Map

Date: 2026-06-03

This is the implementation-oriented companion to
[Baltor Backend Infrastructure Stack](baltor-backend-infrastructure-stack.md).
The stack document defines the strategic backend layers. This research map
catalogs GitHub repos, tools, standards, processes, and evaluation targets that
could become Baltor backend infrastructure.

The key product boundary still holds: Baltor should not be a vector database,
workflow builder, MCP gateway, or generic agent platform. Baltor is the governed
context supply chain that turns raw and already-contextualized inputs into
normalized context objects, claims, relationships, reranked artifacts,
compressed context packs, source handles, lineage, policy decisions, and
context receipts for agents and humans.

## Executive Take

Baltor's backend should be modular:

```text
Context workers / orchestration
Durable worker engine
Source ingestion + parsing
CodeGraph / DocGraph / OrgGraph
Context object registry
Hybrid retrieval
Temporal claim graph
MCP gateway / tool governance
Policy + authorization
Security scanning
Observability + evals
Sandboxed execution
Local/offline memory
```

The product surface should stay stable even when the infrastructure changes:

```text
context_for_ticket()
context_for_mr()
context_for_repo()
context_verify()
context_challenge()
context_fetch()
context_trace()
context_receipt()
```

## Research Boundary

This map should include adjacent tools only when they strengthen Baltor's
verified-context pipeline. A useful tool belongs here if it helps Baltor ingest,
parse, reconcile, verify, enhance, optimize, serve, observe, secure, or reduce
the cost of context work.

Tools that only provide generic agent orchestration, generic workflow editing,
or generic model access should be tracked as backend infrastructure, not product
identity. Free or unofficial model/API routers can be useful for low-risk
background enhancement, but they must be marked low-trust and reverified before
their output can affect certified context.

## 1. Context worker Prototyping

This layer is for workers such as Source Watcher, Reconciler, Fragility Hunter,
Adversarial Interrogator, Context Enhancer, Pack Compressor, and Context Steward
Router.

| Tool / repo | What it is | Baltor fit |
|---|---|---|
| Synapse AI | Visual and open-source multi-agent workflow/orchestration platform. | Good context worker Lab for early visual prototypes. |
| Pydantic AI | Type-safe Python agent framework. | Excellent for structured claim extraction, validated context packs, policy decisions, and receipts. |
| LangGraph | Code-first graph/state-machine agent orchestration. | Strong for wizard flows with explicit state and human-in-the-loop behavior. |
| Microsoft Conductor | YAML/CLI multi-agent workflow runner. | Interesting for context pipelines as code. |
| CrewAI | Role-based crews and structured flows. | Useful when Reconciler, Verifier, Enhancer, and Compressor should be explicit worker roles. |
| Mastra | TypeScript agent framework with workflows, memory, observability, and MCP patterns. | Good fit if Baltor's backend is TypeScript-heavy. |
| LlamaIndex Workflows / Haystack | Document and RAG-oriented workflow frameworks. | Useful for parsing, extraction, retrieval, and pack generation. |
| OpenAI Agents SDK / Google ADK / Microsoft Agent Framework | Provider/platform-native agent frameworks. | Useful for provider-specific integrations, but Baltor should remain provider-neutral. |
| GStack | Garry Tan's open-source skill/workflow pack for Claude Code, Codex, and compatible agents. | Strong reference for role-based delivery loops, QA, review, shipping, retrospectives, and skill packaging; not a context authority. |
| RevFactory Harness | Claude Code meta-skill that designs domain-specific agent teams and generates their skills. | Strong reference for generating Baltor context worker teams, agent definitions, review roles, and skill bundles from a structured request. |
| RevFactory Harness 100 | Catalog of production-grade agent team harnesses across domains. | Useful corpus for studying agent-team patterns, dependency DAGs, trigger boundaries, scale modes, and cross-validation standards. |
| CodexAutoResearch / autoresearch patterns | Agent-driven research workflow pattern; exact repo naming should be verified before adoption. | Useful as a design pattern for repeatable tool discovery, citation capture, and research-to-context promotion. |

Recommended direction:

```text
Pydantic AI for typed context worker outputs
LangGraph or Conductor for structured workflows
Synapse AI for visual experimentation
GStack-style skills for agent-side workflow discipline
RevFactory Harness-style meta-skills for generating domain-specific worker teams
Baltor-owned ContextClaim, SourceHandle, ContextPack, and ContextReceipt contracts
```

GStack's most useful lesson for Baltor is productization: package recurring
agent behavior as installable skills/commands with a clear order. Baltor should
copy that distribution pattern for `context_for_ticket`, `verify_claim`,
`context_trace`, `context_receipt`, repo QA, and pack review skills, while
keeping verified context, source handles, and policy decisions inside Baltor.

RevFactory Harness adds a second useful pattern: generate a domain-specific
agent team and its skills from a request, then enforce structure through agents,
skills, commands, tests, trigger boundaries, and review roles. Baltor should use
this pattern for context worker creation, but every generated worker must still
go through Baltor's agent/tool provenance and CI/CD gates.

## 2. Durable Worker Engines

Context workers run continuously. They need retries, replay, idempotency, audit,
human review, and stateful recovery.

| Tool | What it does | Baltor fit |
|---|---|---|
| Temporal | Durable execution platform with stateful workflows and failure recovery. | Best for mature production-grade long-running workers. |
| Restate | Lightweight durable runtime for agents and workflows. | Strong alternative when Temporal feels too heavy. |
| DBOS | Postgres-backed durable execution. | Attractive for a Postgres-centered Baltor MVP. |
| Inngest | Event-driven durable functions with retries, queues, scaling, and observability. | Good for source webhooks and scheduled refreshes. |
| Hatchet | Durable task and agent orchestration. | Startup-friendly orchestration engine for background workers. |
| Dagster / Prefect | Data and AI pipeline orchestrators. | Better for ingestion, indexing, eval dataset generation, and batch artifacts than agent loops. |
| Cloudflare Workflows / Agents | Durable workflows and agent runtime in Cloudflare's stack. | Good if Baltor is Cloudflare-first. |

Recommended split:

```text
Prototype: DBOS or Inngest
Production SaaS: Temporal or Restate
Data/ingestion jobs: Dagster or Prefect
Cloudflare-native deployment: Cloudflare Workflows
```

## 3. Source Ingestion And Parsing

Baltor needs connectors and document/code normalization before it can verify or
compress context.

| Tool | What it does | Baltor fit |
|---|---|---|
| Airbyte | Connector platform with Jira, Confluence, GitLab, and many other sources. | Good for mirrored/indexed connector pipelines. |
| Unstructured | Open-source preprocessing for PDFs, HTML, Word docs, images, and text. | Good for raw enterprise docs before DocGraph construction. |
| IBM Docling | Document conversion/parsing with advanced PDF understanding. | Strong for local/self-hosted PDF, DOCX, and PPTX parsing. |
| RAGFlow | Open-source RAG engine with agent capabilities. | Useful to study, but Baltor should not collapse into a RAG engine. |
| LlamaIndex / Haystack | RAG/data framework ecosystem. | Useful for connector experiments and retrieval orchestration. |
| dlt / Debezium / CDC tools | Change-data ingestion. | Useful when Baltor needs source-event streams rather than batch crawls. |
| LiteParse | Local open-source document parser from the LlamaIndex ecosystem. | Strong Bronze/source parser for fast local parsing, layout-aware artifacts, screenshots, and parser-lineage capture. |
| Marker / MinerU / PyMuPDF | Specialized document parsing and PDF extraction tools. | Useful parser-router options when LiteParse, Docling, or Unstructured are not the best fit. |
| SchemaSpy | Database schema documentation/visualization tool. | Useful as a data/schema source provider for DocGraph and DataGraph context. |
| DumbAssets / free-app catalogs / awesome lists | Curated public app/tool catalogs; specific repos should be verified before use. | Useful as public source-system examples for tool discovery, not trusted evidence. |
| Network architecture diagram tools / NetViz-like tools | Diagramming and data-driven network architecture visualization. | Useful as architecture-source providers when diagrams contain topology, dependencies, or network policy context. |
| CFPB Consumer Complaint Database | Public official dataset and API for consumer-finance complaints. | Strong public-corpus demo source for source handles, aggregate-only claims, unverified narrative policy, context receipts, and CDC/freshness wiring. |
| SEC EDGAR APIs | Public filings, submissions, and company facts. | Strong DocGraph/financial-risk demo source for filing freshness, fact extraction, and source-qualified financial claims. |
| NIST NVD and CISA KEV | Public vulnerability records and known-exploited-vulnerability catalog. | Strong security-triage demo source when joined with CodeGraph, asset inventory, patch status, and OrgGraph ownership. |
| openFDA | Public FDA APIs and downloads. | Useful high-stakes health-data demo source where reports need causality caveats and aggregate-only guardrails. |
| Data.gov Catalog API | Public metadata catalog for U.S. government datasets. | Useful source-discovery and source-prioritization demo provider. |
| EPA ECHO | Public environmental enforcement/compliance data services. | Useful compliance-pack demo source with facility entities, official-source caveats, and policy-labeled claims. |
| GitHub public repository APIs | Public repo metadata and contents. | Useful CodeGraph/implementation-pack demo source when claims are commit-scoped and raw repo dumps are compressed into code pointers. |

Recommended ingestion process:

```text
source snapshot
-> parser
-> normalized object
-> source handle
-> object hash
-> ACL snapshot
-> context claim extraction
-> graph/retrieval indexes
```

## 4. CodeGraph Infrastructure

CodeGraph is how Baltor understands implementation reality.

| Tool / repo | What it does | Baltor fit |
|---|---|---|
| SCIP | Language-agnostic code indexing protocol for definitions, references, and implementations. | Strong foundation for durable CodeGraph. |
| Serena | MCP toolkit for semantic code retrieval, editing, refactoring, and debugging at symbol level. | Good local CodeGraph/MCP experiment for Claude Code. |
| Sourcegraph MCP | Connects agents to Sourcegraph code intelligence. | Strong provider for enterprise code intelligence. |
| zilliztech/claude-context | MCP plugin that adds semantic code search to Claude Code and coding agents. | Useful local/POC code retrieval layer. |
| Aider repo map | Concise repository map using tree-sitter to summarize important classes/functions. | Excellent pattern for token-efficient CodeGraph summaries. |
| Repomix | Packs repositories into AI-friendly XML, Markdown, JSON, or text and supports MCP. | Good artifact generator; treat outputs as derived context, not truth. |
| GitNexus | Browser/local code knowledge graph with GraphRAG agent. | Worth studying for CodeGraph UX and MCP-native graph patterns. |
| CodeGraphContext | MCP server/CLI toolkit that indexes local code into a graph database. | Directly relevant CodeGraph backend idea. |
| DeepWiki / OpenDeepWiki / deepwiki-open | Generated repo documentation and source-linked explanations. | Good derived artifact provider; generated docs must be commit-scoped and supersedable. |
| CodexSaver / model-routing helpers | MCP-style cost-aware router that delegates low-risk work to cheaper worker models while keeping high-risk judgment with Codex. | Pattern to copy for Baltor's low-trust, low-cost enhancement tier and model-routing policy. |
| Codebase token-saving tools | Repo-map, AST, local MCP, and compact-context tools. | Useful for CodeGraph candidate generation and free-user cost control; outputs remain derived context. |

Recommended pattern:

```text
Repo
-> AST / LSP / SCIP / tree-sitter
-> symbols, files, imports, calls, tests, MRs
-> CodeGraph
-> code pointers and graph paths in context packs
```

## 5. DocGraph Infrastructure

DocGraph represents what the organization says, decided, documented, or
believes.

| Tool / process | What it contributes |
|---|---|
| Docling / Unstructured | Converts PDFs, docs, slides, tables, and pages into structured Markdown/JSON for DocGraph ingestion. |
| llms.txt | Emerging convention for LLM-friendly Markdown indexes at `/llms.txt`. |
| Mintlify / Fern / GitBook AI-native docs | Docs platforms that generate agent-readable docs and Markdown surfaces. |
| Context7 | Fetches up-to-date version-specific docs and examples into coding-agent context. |
| MkDocs / knowledge graph plugins | Useful for docs-as-code and graph-backed doc references. |
| Obsidian / Markdown / Basic Memory | Useful for local/team memory and human-editable context before central promotion. |

DocGraph objects should include:

```text
Document
Section
Decision
Requirement
Claim
Comment
Runbook step
Incident finding
Generated artifact
Source excerpt
```

Every object should carry:

```text
source handle
version/hash
authority
freshness
ACL
lineage
derived_from
supersedes / contradicted_by
```

## 6. OrgGraph Infrastructure

OrgGraph answers who owns this, who can see this, who approves this, and who
should be notified.

| Tool / standard | What it does | Baltor fit |
|---|---|---|
| Backstage | Software catalog for ownership and metadata across services, libraries, data pipelines, and more. | Strong OrgGraph/service-graph provider. |
| EventCatalog | Documents and visualizes event-driven systems. | Good for event/API relationships. |
| Port / Cortex / Compass | Service catalog, ownership, scorecards, readiness, on-call, and compliance. | High-value OrgGraph providers. |
| OpenFGA | Fine-grained relationship-based authorization. | Strong for can_view, can_expand, can_export, and can_promote checks. |
| OPA/Rego | Declarative policy engine. | Good for context-pack policies, DLP gates, and routing decisions. |
| Cedar | Authorization policy language. | Good for application-style fine-grained authorization. |
| CODEOWNERS / PagerDuty / Slack / Teams / IdP | Ownership, on-call, escalation, and group membership. | OrgGraph enrichment inputs. |

Baltor should resolve:

```text
repo -> service -> owner team -> on-call -> required approver -> access policy
```

## 7. Graph And Temporal Memory Backends

This layer stores relationships, claims, contradictions, and changes over time.

| Tool | What it does | Baltor fit |
|---|---|---|
| Graphiti / Zep | Temporal knowledge graph memory for frequently changing context. | Strong candidate for temporal claim graphs. |
| Neo4j GraphRAG | Graph database and GraphRAG ecosystem. | Mature enterprise graph path. |
| Microsoft GraphRAG | Extracts structured graph data from unstructured text for graph/community RAG. | Useful for batch DocGraph construction. |
| Cognee | Open-source memory platform combining embeddings and graphs. | Good graph-memory experiment. |
| Kuzu | Embedded graph database. | Strong local/offline CodeGraph and DocGraph option. |
| FalkorDB / GraphRAG SDK | GraphRAG toolkit with graph traversal. | Good self-hosted graph-RAG option. |
| TypeDB | Semantic/hypergraph modeling. | Useful if n-ary claims and approval relationships become central. |
| ArangoDB / SurrealDB / Memgraph / HelixDB | Multi-model or graph/vector stores. | Worth POCs for graph + vector in one layer. |

Layered storage model:

```text
Postgres = canonical registry
Graph DB = relationship/path queries
Vector/hybrid search = candidate retrieval
Object store = raw/derived artifacts
```

## 8. Hybrid Retrieval Backends

Baltor needs keyword, exact handle, vector, metadata, graph, and reranking.
Engineering context cannot rely on vectors alone.

| Backend | Strength |
|---|---|
| Qdrant | Strong vector/hybrid retrieval with metadata payload filters. |
| Weaviate | Hybrid search combining vector and BM25F with configurable fusion. |
| OpenSearch / Elasticsearch | Mature BM25/search infrastructure with vector and hybrid options. |
| Azure AI Search | Microsoft enterprise option with hybrid full-text + vector search. |
| Vespa | Strong for custom ranking and large-scale hybrid search. |
| LanceDB / Chroma / SQLite vector extensions | Good for local/offline memory and developer-side search. |
| Pinecone / Milvus / Zilliz | Managed or large-scale vector infrastructure; not complete context layers alone. |

Recommended retrieval pattern:

```text
Local:
  SQLCipher + sqlite-vec / LanceDB

Team SaaS:
  Postgres + Qdrant / Weaviate

Enterprise:
  Postgres + OpenSearch / Azure AI Search / Vespa + graph store
```

## 9. MCP Gateway And Tool Governance

Baltor should expose context tools through a governed MCP gateway rather than
directly exposing every raw source tool.

| Tool | What it does | Baltor fit |
|---|---|---|
| Cloudflare MCP Server Portals | Centralizes MCP servers behind one endpoint with Access policies. | Strong Cloudflare-first option. |
| IBM Context Forge | Open-source registry/proxy federating MCP, A2A, REST, and gRPC APIs. | Strong self-hosted enterprise option. |
| Portkey MCP Gateway | MCP proxy with auth, access control, credential injection, permission checks, and logging. | Strong managed/control-plane candidate. |
| TrueFoundry MCP Gateway | Enterprise MCP gateway with registry and centralized auth. | Strong VPC/private-cloud option. |
| ToolHive | Runs, governs, and connects MCP servers with local, desktop, CLI, Kubernetes, and registry surfaces. | Strong local/Kubernetes secure MCP fleet option. |
| Arcade / Composio / Pipedream / Nango | Tool auth/action connector layers. | Useful for action-capable connectors, not Baltor's context authority. |

Recommended public surface:

```text
baltor.context_for_ticket
baltor.context_for_mr
baltor.context_for_repo
baltor.context_verify
baltor.context_fetch
baltor.context_trace
baltor.context_receipt
```

Hide or restrict:

```text
raw_jira_get_all_comments
raw_confluence_export_space
raw_gitlab_full_diff
raw_repo_dump
```

## 10. MCP And Agent Security Tools

MCP and agent supply-chain safety should be part of Baltor's backend from the
beginning.

| Tool / repo | What it does | Baltor fit |
|---|---|---|
| Snyk Agent Scan | Inventories and scans agent components, MCP servers, and skills. | Add to CI and local developer setup. |
| Ramparts | Security scanner for MCP servers and AI agent skills. | Good second scanner. |
| Invariant MCP-Scan | Scans for MCP tool poisoning and rug-pull attacks. | Important for MCP supply-chain safety. |
| Cisco MCP Scanner | Scans MCP servers/tools using multiple scanning engines. | Worth watching for enterprise security. |
| ToolHive isolation | Runs MCP servers in isolated containers with minimal permissions. | Good runtime containment. |
| GitHub secret scanning / Gitleaks / Semgrep | Secret and static analysis for repo artifacts and generated context. | Needed for raw source ingestion and context-pack generation. |
| ZAP / Nuclei / Wapiti / other scanners | Web and infrastructure scanners. | Useful as security-source providers and context worker checks for exposed services, not as context truth by themselves. |

Baltor-specific security process:

```text
scan MCP manifests
hash tool definitions
scan skills/CLAUDE.md/AGENTS.md
scan generated context packs
scan source excerpts before promotion
block raw expansion on high-risk findings
record policy decision in context receipt
```

## 11. Observability And Evals

Baltor needs generic LLM observability plus context-specific evals.

| Tool | What it provides | Baltor fit |
|---|---|---|
| Langfuse | Open-source LLM monitoring, evaluation, and debugging. | Strong self-hostable trace/eval platform. |
| Arize Phoenix | Open-source AI observability, evaluation, and troubleshooting. | Good for RAG/context eval labs. |
| Braintrust | Evaluation, tracing, experimentation, and regression detection. | Strong enterprise eval workflow. |
| DeepEval | Pytest-like LLM evaluation framework. | Good unit/regression tests for context packs. |
| Ragas / TruLens | RAG metrics such as faithfulness and context precision. | Useful, but Baltor needs stale-source and policy-aware metrics too. |
| OpenLLMetry / OpenTelemetry GenAI | Vendor-neutral LLM and GenAI instrumentation. | Use as trace schema foundation. |
| Helicone / OpenLIT | AI gateway and observability options. | Useful for model-call gateway observability. |
| otel-gui / otel-desktop-viewer / otel-tui | Local OpenTelemetry trace viewers. | Useful for developer-local debugging of context worker traces before sending telemetry to a vendor. |
| Prometheus / Grafana | Metrics collection and dashboards. | Useful for worker health, queue depth, source freshness, drift alerts, and pack-generation SLOs. |

Baltor-specific evals:

```text
source recall
claim citation coverage
source-handle validity
stale-source detection
conflict detection
ACL correctness
raw expansion rate
pack token budget
developer usefulness
agent task success
context receipt completeness
```

Normal RAG metrics are not enough. A response can be faithful to retrieved
context while the retrieved context itself is stale, unauthorized, or wrong.

## 12. AI Infrastructure And Operations

These tools are not Baltor primitives, but they matter when Baltor needs to run
workers, evaluate models, serve local/self-hosted inference, or operate in
Kubernetes-heavy environments.

| Tool | What it provides | Baltor fit |
|---|---|---|
| Argo CD | GitOps deployment for Kubernetes. | Deploy Baltor workers, gateways, policies, and graph/retrieval services from versioned config. |
| KEDA | Kubernetes event-driven autoscaling. | Autoscale context workers from source events, queue depth, MR activity, or eval backlogs. |
| Kubeflow | Kubernetes ML workflows. | Useful only if Baltor trains or operates custom extraction, reranking, or classification models. |
| MLflow | ML lifecycle tracking and model registry. | Useful for model experiments, custom rerankers, extraction models, and evaluation lineage. |
| vLLM | High-throughput LLM serving. | Useful for self-hosted extraction, summarization, reranking, or free-tier/background inference. |
| NVIDIA Triton / TensorRT-LLM / Dynamo | Inference serving and optimization stack. | Later-stage infrastructure for enterprise/self-hosted GPU inference and high-throughput model serving. |
| Docker MCP Tutorial / Docker MCP Toolkit examples | Containerized MCP server tutorials and examples. | Good training/template material for building Baltor MCP tools that run in containers. |

Use these as an operations layer:

```text
Baltor core:
  verified context objects, source handles, claims, receipts, source precedence

Operations layer:
  Argo CD, KEDA, OpenTelemetry, Prometheus, Grafana, MLflow, vLLM, Triton
```

## 13. Low-Cost And Backup Model Routing

Free, unofficial, or low-cost API routers can help free users and background
workers, but they must never become a source of certified truth.

`chatanywhere/GPT_API_free` is the current concrete example to support in a
non-commercial demo environment. Treat it as an OpenAI-compatible demo route,
not a production provider. See
[Baltor Free LLM Demo Routing](baltor-free-llm-demo-routing.md) for the route
policy and environment wiring.

Good uses:

```text
low-risk draft enhancement
public-source summarization
background candidate generation
cheap search/explanation work
backup processing when paid providers are unavailable
free-user slow queue
```

Blocked uses:

```text
customer private data
policy decisions
final verification
regulated workflows
source-handle expansion for sensitive sources
context receipts that claim certified provenance
```

Provider-tier metadata should be explicit:

```json
{
  "provider_tier": "non_commercial_demo | free_best_effort",
  "trust_level": "low",
  "commercial_use": "non_commercial_only",
  "allowed_environments": ["demo_noncommercial", "local_demo"],
  "allowed_for": ["draft_enhancement", "background_summary"],
  "blocked_for": ["verification", "policy", "private_sources"],
  "requires_reverification": true
}
```

## 14. Agent Harnesses, Skill Generation, And Self-Improving Workers

This category is directly relevant to Baltor's backend-agent CI/CD. These tools
and research systems explore how an agent recognizes missing capabilities,
creates or installs skills, spawns sub-agents, or evolves its harness over time.

The Baltor rule is strict: self-improving harnesses can propose or draft new
workers, skills, commands, tools, and sub-agents, but Baltor must gate them with
creation provenance, policy, evals, and release approval before they affect
verified context.

| Tool / research | What it does | Baltor fit |
|---|---|---|
| Hermes Agent | Self-hosted agent with persistent memory, reusable skills, automated skill creation, scheduled automation, tools, and multi-platform chat. | Strong reference for recognizing repeated successful workflows and turning them into reusable skills. |
| OpenClaw | Open-source local agent runtime with skills, MCP integration, memory, sub-agent spawning, ACP harness support, messaging channels, and automation. | Strong reference for sub-agent spawning, skill runtime boundaries, and agent-skill supply-chain risk. |
| Superpowers | Cross-platform agentic skills framework and software development methodology for coding agents. | Useful reference for spec-first, TDD, review, and verification workflows packaged as skills. |
| RevFactory Harness / Harness 100 | Meta-skill and catalog for generating specialized agent teams and domain-specific skills. | Good reference for Baltor-generated context worker teams and skill bundles. |
| GStack | Agent workflow and skill pack for Claude Code, Codex, and compatible agents. | Good reference for agent-side shipping loops and command packaging. |
| uberSKILLS | Visual/AI-assisted skill designer and deployment tool for multiple coding agents. | Useful reference for skill authoring UX, validation, and cross-agent distribution. |
| AgentCrew | Containerized multi-agent orchestration with roles, instructions, skills, isolated filesystems, and pub/sub. | Useful reference for isolated context worker teams and agent-to-agent coordination. |
| AgentMint | Pay-as-you-go subagent marketplace that binds harness, model, keys, and skills. | Useful market signal for sub-agent packaging, not a Baltor trust layer. |
| Supyagent | Agent tool/skills platform that can generate skills and connect agents to services/data sources. | Useful as action/tool connector and skill-generation reference. |
| Open Agent Skills / OpenAgent.bot / AAM-style directories | Skill and agent directories/marketplaces. | Useful discovery sources; treat as untrusted supply-chain inputs that require scanning and provenance. |
| MetaAgent | Research on tool meta-learning where agents build in-house tools and persistent knowledge from tool-use history. | Strong conceptual reference for Baltor's "suggest a deterministic worker" loop. |
| Memento-Skills | Research system where agents design task-specific agents through evolving structured skills and memory. | Strong reference for autonomous skill evolution with persistent markdown-like skills. |
| Affordance Agent Harness | Verification-gated skill orchestration with evidence store, memory priors, cost control, and router-selected skills. | Very aligned with Baltor's verification-gated tool/skill selection model. |
| Agentic Harness Engineering | Research on observability-driven automatic evolution of coding-agent harnesses. | Directly relevant to measuring worker outcomes and evolving tools/middleware/memory. |
| SWE-Skills-Bench | Benchmark for evaluating whether skills help real-world software engineering tasks. | Useful eval model for Baltor skill effectiveness and regression testing. |

Use these systems to design a Baltor loop:

```text
production signal or user request
-> detect repeated gap / failure / high-cost manual pattern
-> propose skill, sub-agent, tool, or deterministic worker
-> record creation provenance
-> generate draft artifact
-> run scans and evals
-> steward review
-> canary release
-> monitor usefulness, cost, and safety
-> promote, revise, or revoke
```

Potential gap signals:

```text
same context conflict appears repeatedly
human steward repeats the same resolution
agent repeatedly requests raw expansion for the same source type
pack generation has high cost for a repeated workflow
worker fails on a recurring file/doc/API shape
eval suite exposes a stable missing capability
security scanner flags repeated tool/skill pattern
```

Possible generated artifacts:

```text
agent skill
sub-agent profile
deterministic parser
schema normalizer
source connector
MCP tool wrapper
verification rule
policy check
eval fixture
pack blueprint
context receipt field
```

Generated artifacts must default to `draft` and remain blocked from production
until they pass Baltor's agent/tool creation provenance and CI/CD gates.

## 15. Sandboxed Execution

Context workers will eventually run code analysis, tests, parsers, and untrusted
transformations. That requires isolation.

| Tool | What it does | Baltor fit |
|---|---|---|
| E2B | Secure cloud runtime for AI applications and agents. | Good fast path for agent code execution. |
| Daytona | Fast, stateful agent/dev sandboxes. | Good for repo/workspace analysis. |
| Modal Sandboxes | Secure containers for untrusted user/agent code at scale. | Strong for high-scale source processing and evals. |
| Cloudflare Sandbox SDK / Dynamic Workers | Cloudflare-native sandboxing and dynamic execution. | Good if Baltor is Cloudflare-first. |
| Firecracker / gVisor / Kata | Lower-level isolation primitives. | Best for regulated/self-hosted deployments. |

Use sandboxes for:

```text
repo parsing
test execution
untrusted artifact processing
generated-code checks
LLM-produced transformation scripts
third-party connector validation
```

## 16. Local And Offline Memory

Baltor should support split-brain memory: private local memory can work offline
and be encrypted or E2EE-synced, while company context is centrally governed and
searchable by approved services.

| Tool / repo | What it does | Baltor fit |
|---|---|---|
| Basic Memory | Local-first semantic knowledge graph with MCP integration. | Strong Phase 1 local memory experiment. |
| Claude-Mem | Persistent memory for Claude Code. | Worth studying; Baltor should add governance and promotion. |
| CodexSaver-style worker routing | Local/global MCP routing pattern for cheaper worker models. | Useful for free-user slow queues and low-risk delegated enhancement, not verified context. |
| GStack | Installable Claude Code/Codex workflow skills and commands. | Useful as a model for Baltor skills that teach agents how to request verified context, run review, QA, and ship with context receipts. |
| RevFactory Harness / Harness 100 | Meta-skill and catalog for generating specialized agents and skills. | Useful as a model for Baltor-generated context worker teams and domain-specific skill packs, subject to provenance and release gates. |
| Hermes Agent | Persistent agent memory and automated skill creation. | Useful reference for letting successful repeated workflows become draft skills, subject to Baltor review gates. |
| OpenClaw | Skills, MCP, memory, and sub-agent spawning runtime. | Useful reference for sub-agent execution and skill supply-chain controls. |
| Superpowers | Agentic skills framework and software development methodology. | Useful reference for spec, TDD, review, and verification packaged as skills. |
| Obsidian / Markdown vault | Human-readable local context. | Best initial memory format. |
| SQLCipher | Encrypted SQLite. | Strong local encrypted memory store. |
| sqlite-vec / SQLite Vector | Local vector search inside SQLite. | Good offline search over local memory. |
| ElectricSQL / PowerSync / Replicache / Automerge | Local-first sync patterns. | Useful for encrypted sync/event-log designs. |
| LanceDB / Chroma | Local vector stores. | Good local context cache candidates. |

Recommended local-memory architecture:

```text
SQLCipher memory.db
+ sqlite-vec / LanceDB local index
+ Markdown export/import
+ encrypted event sync queue
+ source handles
+ TTL/freshness labels
+ promotion workflow
```

## 17. Standards And Schemas

These matter because Baltor's moat is partly the context contract.

| Standard / technology | Use in Baltor |
|---|---|
| JSON Schema | Validate context objects, packs, receipts, and connector manifests. |
| JSON-LD / schema.org | Linked semantic objects and portable context metadata. |
| W3C PROV / PROV-O | Provenance model for source, derivation, and lineage. |
| OpenLineage | Source ingestion and pipeline lineage. |
| OpenTelemetry GenAI | Vendor-neutral model/tool traces. |
| OpenFGA / Zanzibar model | Relationship-based authorization for context objects and source handles. |
| OPA/Rego or Cedar | Policy-as-code for context use, expansion, export, and routing. |
| llms.txt / AGENTS.md / CLAUDE.md / SKILL.md | Agent-readable docs, rules, and context entry points. |
| SCIP / LSIF / Tree-sitter / LSP | CodeGraph construction. |
| CycloneDX / SPDX | Software supply-chain context. |
| STIX/TAXII | Security context. |
| FHIR / XBRL / ISO 20022 / EPCIS / IFC | Future regulated or industry-specific packs. |

## 18. Backend Processes To Formalize

### Context CI/CD

Every context artifact should go through a pipeline like code:

```text
source event
-> snapshot
-> parse
-> normalize
-> source-handle validation
-> ACL snapshot
-> prompt-injection scan
-> claim extraction
-> reconciliation
-> anti-fragility scoring
-> enhancement
-> verification/interrogation
-> compression/prioritization
-> context receipt
-> publish pack
-> observe usage
```

### Source-Handle Contract

Every durable claim must include:

```json
{
  "claim": "...",
  "source_handles": ["ctx://..."],
  "evidence_type": "decision | code | comment | test | generated_artifact",
  "freshness": "...",
  "authority": "...",
  "policy": "...",
  "valid_until": "..."
}
```

### Context Promotion Workflow

```text
private_local
-> proposed_repo_memory
-> team_reviewed
-> org_approved_cache
-> company_context
```

Promotion requires:

```text
source handles
TTL
classification
reviewer / steward
prompt-injection scan
conflict check
policy decision
```

### Context Receipt

Every served pack should emit:

```json
{
  "pack_id": "...",
  "user": "...",
  "agent": "Claude Code",
  "task_type": "implementation",
  "sources_used": [],
  "claims_included": [],
  "claims_excluded": [],
  "conflicts_disclosed": [],
  "policy_decision": "...",
  "ttl": "...",
  "retrieval_policy": "...",
  "reranker": "...",
  "compressor": "...",
  "trace_id": "..."
}
```

### Context Drift Monitor

Continuously detect:

```text
code contradicts docs
Jira changed after pack generation
MR changed after review pack
generated repo wiki stale against commit
owner changed in OrgGraph
permission changed on source handle
local memory claim expired
```

## 19. Shortlist To Test First

| Area | Tools |
|---|---|
| Context worker layer | Pydantic AI, LangGraph, Microsoft Conductor, Synapse AI |
| Durable execution | DBOS, Restate, Temporal, Inngest |
| Source ingestion | Airbyte, Docling, LiteParse, Unstructured, LlamaIndex |
| CodeGraph | SCIP, Serena, Aider repo map, Repomix, Sourcegraph MCP, GitNexus, CodeGraphContext |
| DocGraph | Docling, Unstructured, llms.txt, Context7, Basic Memory, Obsidian |
| OrgGraph / policy | Backstage, EventCatalog, OpenFGA, OPA/Rego, Cedar |
| Retrieval / graph | Postgres, Qdrant or Weaviate, OpenSearch, Graphiti or Neo4j, Kuzu |
| MCP/security | ToolHive, IBM Context Forge, Cloudflare MCP Portals, Snyk Agent Scan, Ramparts, Invariant MCP-Scan |
| Observability/evals | OpenTelemetry GenAI, otel-gui, Langfuse, Phoenix, Braintrust, DeepEval, Ragas, Prometheus, Grafana |
| AI infra / operations | Argo CD, KEDA, MLflow, Kubeflow, vLLM, Triton, Dynamo |
| Agent skill distribution | GStack, RevFactory Harness, Harness 100, GitHub/Vercel-style skills, SkillHub, Skills-Manager, HarnessKit |
| Agent harness / skill generation | Hermes Agent, OpenClaw, Superpowers, uberSKILLS, AgentCrew, MetaAgent, Memento-Skills, Affordance Agent Harness |
| Sandbox | E2B, Daytona, Modal, Firecracker/gVisor/Kata |

## 20. Suggested 30-Day Research Plan

### Week 1: Local Context + Code Graph

Build:

```text
Claude Code -> local Baltor MCP
Baltor MCP -> Serena / Repomix / Aider repo map
Baltor MCP -> Basic Memory / Markdown vault
```

Deliver:

```text
context_for_repo()
context_for_ticket() stub
source-handle format v0
local memory promotion rules
```

### Week 2: Source Ingestion + Packs

Build:

```text
Jira/Confluence/GitLab read adapters
Docling/Unstructured parser
implementation_pack schema
context_receipt schema
```

Deliver:

```text
context_for_ticket(ticket, repo)
```

### Week 3: Verification And Drift

Add:

```text
Pydantic AI claim extractor
DBOS/Inngest durable workflow
OpenFGA/OPA policy check
Snyk Agent Scan / Ramparts CI scan
```

Deliver:

```text
context_verify()
context drift report
```

### Week 4: Eval And Gateway

Add:

```text
Langfuse/Phoenix tracing
DeepEval/Ragas pack tests
ToolHive or Context Forge gateway
```

Deliver:

```text
context_trace()
pack eval dashboard
MCP gateway deployment sketch
```

## Final Recommendation

Treat these tools as infrastructure primitives, not product identity.

Baltor should own:

```text
verified context object model
source handles
claim/evidence graph
context-pack schemas
context receipts
source precedence
context drift detection
policy-aware delivery
local-to-cloud memory boundary
```

Use open-source and commercial tools underneath:

```text
Pydantic AI / LangGraph / Conductor to run wizards
DBOS / Restate / Temporal / Inngest for durable execution
Docling / Unstructured / Airbyte for ingestion
SCIP / Serena / Sourcegraph / Repomix for CodeGraph
Backstage / OpenFGA / OPA for OrgGraph and policy
Graphiti / Neo4j / Kuzu for relationships
Qdrant / Weaviate / OpenSearch for retrieval
ToolHive / Context Forge / Cloudflare / Portkey for MCP governance
Langfuse / Phoenix / Braintrust for observability and evals
E2B / Daytona / Modal / Firecracker for sandboxed execution
```

The product should feel simple to agents:

```text
Ask Baltor for context.
Baltor reconciles, interrogates, enhances, compresses, and certifies it.
Agent receives the smallest safe context pack with source handles and a receipt.
```

## Reference Links

- Pydantic AI durable execution: <https://pydantic.dev/docs/ai/integrations/durable_execution/overview/>
- GStack site: <https://gstack.lol/>
- GStack GitHub: <https://github.com/garrytan/gstack>
- RevFactory Harness: <https://github.com/revfactory/harness>
- RevFactory Harness 100: <https://github.com/revfactory/harness-100>
- RevFactory Claude Code Harness experiment: <https://github.com/revfactory/claude-code-harness>
- Hermes Agent: <https://hermes-agent.org/>
- OpenClaw sub-agents: <https://docs.openclaw.ai/subagents>
- OpenClaw ACP agents: <https://docs.openclaw.ai/tools/acp-agents>
- Superpowers: <https://github.com/obra/superpowers>
- uberSKILLS: <https://uberskills.dev/>
- AgentCrew: <https://agentcrew.sh/>
- AgentMint: <https://agentmint.store/>
- Supyagent: <https://supyagent.com/>
- Open Agent Skills: <https://openagentskills.dev/>
- OpenAgent.bot: <https://www.openagent.bot/>
- MetaAgent: <https://arxiv.org/abs/2508.00271>
- Memento-Skills: <https://arxiv.org/abs/2603.18743>
- Affordance Agent Harness: <https://arxiv.org/abs/2605.00663>
- Agentic Harness Engineering: <https://arxiv.org/abs/2604.25850>
- SWE-Skills-Bench: <https://arxiv.org/abs/2603.15401>
- Microsoft Conductor: <https://opensource.microsoft.com/blog/2026/05/14/conductor-deterministic-orchestration-for-multi-agent-ai-workflows/>
- Temporal: <https://temporal.io/>
- Restate AI agents: <https://docs.restate.dev/use-cases/ai-agents>
- DBOS AI quickstart: <https://docs.dbos.dev/ai/ai-quickstart>
- Inngest durable execution: <https://www.inngest.com/docs/learn/how-functions-are-executed>
- Hatchet docs: <https://docs.hatchet.run/>
- Dagster: <https://dagster.io/>
- Airbyte Jira connector: <https://docs.airbyte.com/integrations/sources/jira>
- Unstructured: <https://github.com/Unstructured-IO/unstructured>
- Docling: <https://github.com/docling-project/docling>
- LiteParse: <https://github.com/run-llama/liteparse>
- SchemaSpy: <https://github.com/schemaspy/schemaspy>
- Marker: <https://github.com/datalab-to/marker>
- MinerU: <https://github.com/opendatalab/MinerU>
- RAGFlow: <https://github.com/infiniflow/ragflow>
- SCIP: <https://github.com/scip-code/scip>
- Serena: <https://github.com/oraios/serena>
- Sourcegraph MCP: <https://sourcegraph.com/mcp>
- Claude Context: <https://github.com/zilliztech/claude-context>
- Aider repo map: <https://aider.chat/docs/repomap.html>
- Repomix: <https://github.com/yamadashy/repomix>
- GitNexus: <https://github.com/abhigyanpatwari/GitNexus>
- CodeGraphContext: <https://github.com/CodeGraphContext/CodeGraphContext>
- DeepWiki Open: <https://github.com/AsyncFuncAI/deepwiki-open>
- llms.txt: <https://llmstxt.org/>
- Mintlify agent context: <https://www.mintlify.com/blog/context-for-agents>
- Context7: <https://github.com/upstash/context7>
- MkRefs: <https://github.com/DerwenAI/mkrefs>
- Basic Memory: <https://docs.basicmemory.com/>
- Backstage Software Catalog: <https://backstage.io/docs/features/software-catalog/>
- EventCatalog Backstage plugin: <https://github.com/event-catalog/backstage-plugin-eventcatalog>
- OpenFGA: <https://openfga.dev/>
- OPA: <https://openpolicyagent.org/docs>
- Cedar: <https://docs.cedarpolicy.com/>
- Graphiti overview: <https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/>
- FalkorDB GraphRAG SDK: <https://github.com/FalkorDB/GraphRAG-SDK/>
- sqlite-vec: <https://github.com/asg017/sqlite-vec>
- IBM Context Forge: <https://github.com/IBM/mcp-context-forge>
- TrueFoundry MCP Gateway: <https://www.truefoundry.com/blog/introducing-truefoundry-mcp-gateway>
- ToolHive: <https://docs.stacklok.com/toolhive/>
- Snyk Agent Scan: <https://github.com/snyk/agent-scan>
- Ramparts: <https://github.com/getjavelin/ramparts>
- Invariant MCP-Scan: <https://invariantlabs.ai/blog/introducing-mcp-scan>
- Cisco MCP Scanner: <https://github.com/cisco-ai-defense/mcp-scanner>
- OWASP ZAP: <https://github.com/zaproxy/zaproxy>
- Nuclei: <https://github.com/projectdiscovery/nuclei>
- Langfuse: <https://github.com/langfuse/langfuse>
- Phoenix: <https://github.com/arize-ai/phoenix>
- DeepEval: <https://github.com/confident-ai/deepeval>
- OpenLLMetry: <https://github.com/traceloop/openllmetry>
- otel-gui: <https://github.com/metoro-io/otel-gui>
- Prometheus: <https://github.com/prometheus/prometheus>
- Grafana: <https://github.com/grafana/grafana>
- Argo CD: <https://github.com/argoproj/argo-cd>
- KEDA: <https://github.com/kedacore/keda>
- Kubeflow: <https://github.com/kubeflow/kubeflow>
- MLflow: <https://github.com/mlflow/mlflow>
- vLLM: <https://github.com/vllm-project/vllm>
- NVIDIA Triton Inference Server: <https://github.com/triton-inference-server/server>
- NVIDIA Dynamo: <https://github.com/ai-dynamo/dynamo>
- Docker MCP Tutorial: <https://github.com/NetworkChuck/docker-mcp-tutorial>
- Atlan LLM evaluation comparison: <https://atlan.com/know/llm-evaluation-frameworks-compared/>
- Awesome Sandbox: <https://github.com/restyler/awesome-sandbox>
- Modal sandbox comparison: <https://modal.com/resources/best-code-execution-sandboxes-ai-agents>
- Basic Memory GitHub: <https://github.com/basicmachines-co/basic-memory>
- Claude-Mem: <https://github.com/thedotmack/claude-mem>
- SQLCipher: <https://github.com/sqlcipher/sqlcipher>
- W3C PROV-DM: <https://www.w3.org/TR/prov-dm/>
- OpenTelemetry GenAI semantic conventions: <https://opentelemetry.io/docs/specs/semconv/gen-ai/>
