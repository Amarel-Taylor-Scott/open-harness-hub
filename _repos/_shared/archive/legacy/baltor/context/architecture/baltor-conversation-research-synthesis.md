# Baltor Conversation Research Synthesis

Date: 2026-06-04

This document consolidates the major product, architecture, visual, and backend
research conclusions from the Baltor conversation. It is a synthesis layer, not
a replacement for the detailed architecture notes.

## North Star

Baltor is **CI/CD for enterprise context**.

Agents, copilots, dashboards, and workflow platforms increasingly have
deployment, identity, monitoring, and evaluation lifecycles. Context needs the
same release discipline:

```text
source changes
-> context builds
-> verification checks
-> policy gates
-> promotion states
-> context receipts
-> serving
-> monitoring
-> rollback / revalidation
```

Baltor should own the verified context contract:

```text
context objects
source handles
claims and evidence
relationships
source precedence
freshness / TTL
policy decisions
context packs
context receipts
context drift detection
local-to-cloud memory boundary
```

Baltor should not become:

```text
a generic agent builder
a generic workflow canvas
a vector database
an MCP gateway
a raw enterprise search tool
a model provider router
```

Those are backend/provider layers.

## Product Positioning

Best short form:

> Baltor is CI/CD for enterprise context.

Expanded:

> Baltor verifies, reconciles, enhances, compresses, and certifies
> organizational context before AI workflows, coding tools, dashboards, and
> humans use it.

Microsoft Foundry, GitHub agents, Harness AI DevOps Agents, OpenAI Agents, and
similar platforms are building CI/CD around agents. Baltor's wedge is the
parallel layer for context:

```text
Agent CI/CD = lifecycle of the worker
Context CI/CD = lifecycle of the knowledge the worker consumes
```

## Core Flow

The main conceptual flow remains:

```text
Source Systems
-> Reconciliation
-> Anti-Fragility
-> Enhancement
-> Optimization
-> Consumption

Universal rail:
Continuous Verification + Adversarial Validation
```

The universal rail checks every stage for:

```text
contradictions
source precedence
fragile facts
missing evidence
freshness
prompt-injection risk
policy risk
ACL violations
```

## Visual Direction

The best visual direction from the page iterations is:

```text
compact dark dashboard
wide animated canvas
visible vertical partitions
low-noise centered assurance rail
stage details by hover/focus
dedicated pages per stage
context wizard rails linked to stage pages
```

Avoid:

```text
large inspector modules inside the canvas
button-heavy diagram overlays
extra text above the flow
medallion naming as a primary brand
overlarge orbit/ring effects
unverified "oracle" language
```

Use:

```text
Baltor Context Engine
Context Wizard Rails
Continuous Verification + Adversarial Validation
Source Systems / Reconciliation / Anti-Fragility / Enhancement / Optimization / Consumption
```

## Graph-Of-Graphs

CodeGraph, DocGraph, and OrgGraph should be specialized providers inside
Baltor's Context Object Fabric:

```text
CodeGraph = how the system works
DocGraph  = what the organization says, decided, or documented
OrgGraph  = who owns, approves, accesses, and is affected

Baltor Overlay Graph = reconciled, verified, source-linked context paths
```

Example path:

```text
Jira BILL-782
-> ADR-014 retry policy
-> RetryScheduler.scheduleRetry
-> retry_scheduler.test.ts
-> billing-platform owner
-> required reviewer group
```

The graph is not the product by itself. The product is the verified context pack
and its receipt.

## Context CI/CD

Context CI/CD should become a formal Baltor operating model:

```text
source event
-> snapshot
-> parse
-> normalize
-> source-handle validation
-> ACL snapshot
-> prompt-injection / secret scan
-> claim extraction
-> reconciliation
-> anti-fragility scoring
-> enhancement
-> verification / adversarial validation
-> evals
-> optimization / compression
-> context receipt
-> publish pack
-> monitor drift
```

Promotion states:

```text
raw_snapshot
parsed_object
candidate_claim
machine_verified
verified_with_conflicts
steward_reviewed
org_approved
published_pack
expired
superseded
revoked
```

## Backend-Agent CI/CD

The Context Wizards that operate Baltor also need CI/CD:

```text
Source Watcher
Parser Worker
Claim Extractor
Reconciler
Fragility Hunter
Adversarial Interrogator
Enhancer
Optimizer / Compressor
Policy Checker
Receipt Builder
Context Steward Router
Drift Monitor
```

Each worker release includes:

```text
worker code
prompt / instruction bundle
model routing policy
tool allowlist
input schema
output schema
eval dataset
reference fixtures
policy hooks
rollback version
observability schema
```

The critical rule:

> A worker is not just code. Its prompts, models, tools, schemas, evals, and
> policies are part of the release.

## Agent And Tool Creation Provenance

Every new agent, bot, worker, tool, skill, command, parser, scanner, connector,
or MCP server should have provenance for the **decision to create it**, not only
for source code.

Baltor should record:

```text
who requested it
when it was requested
where the request originated
why it was needed
what alternatives were considered
how the decision was made
who or what approved it
which sources/evidence justified it
which risks were identified
which context packs, incidents, tickets, eval failures, or drift reports led to it
```

Generated or self-improving artifacts default to `draft` until they pass:

```text
creation provenance
security scans
MCP/skill manifest scans
schema validation
evals
policy review
canary release
steward approval when needed
rollback metadata
```

## Self-Improving Harnesses

Tools and research systems such as Hermes Agent, OpenClaw, RevFactory Harness,
GStack, Superpowers, uberSKILLS, AgentCrew, MetaAgent, Memento-Skills,
Affordance Agent Harness, and Agentic Harness Engineering are useful because
they point toward a future loop:

```text
detect repeated gap / failure / expensive manual pattern
-> propose skill, sub-agent, tool, or deterministic worker
-> record creation provenance
-> generate draft artifact
-> scan and eval
-> steward review
-> canary release
-> monitor usefulness, cost, and safety
-> promote, revise, or revoke
```

This is strategically important, but it must not bypass Baltor governance.

## Agent Skills As Supply Chain

GitHub, OpenAI/Codex, LangChain, GStack, RevFactory Harness, Superpowers, and
other ecosystems are normalizing skills as portable bundles of instructions,
scripts, and resources.

For Baltor, skills are a delivery and workflow layer:

```text
context_for_ticket skill
verify_claim skill
context_trace skill
context_receipt skill
review_context_pack skill
repo_context skill
api_context skill
local_memory_promotion skill
```

Skills should be governed like code:

```text
source repo
owner
version
tool permissions
MCP dependencies
policy scope
tests
evals
changelog
approval state
distribution target
```

## Provider Layers

Baltor should maintain a modular provider architecture.

Parser Manager:

```text
LiteParse
Docling
Unstructured
Marker
MinerU
PyMuPDF
```

Repo Directory / CodeGraph:

```text
Serena
Repomix
Sourcegraph MCP
SCIP
tree-sitter
CodeGraphContext
GitNexus
```

DocGraph:

```text
Confluence
Jira
ADRs
generated repo docs
llms.txt
Context7
Basic Memory
SchemaSpy
network architecture diagrams
```

OrgGraph and policy:

```text
Backstage
Port
Cortex
Compass
OpenFGA
OPA
Cedar
CODEOWNERS
PagerDuty
IdP
```

Scraping Manager:

```text
Firecrawl
Crawl4AI
Scrapy
Playwright
Browserless
Apify / Bright Data
```

MCP gateway and security:

```text
Cloudflare MCP Portals
IBM Context Forge
ToolHive
Portkey
TrueFoundry
Snyk Agent Scan
Ramparts
Invariant MCP-Scan
Cisco MCP Scanner
```

Observability and evals:

```text
OpenTelemetry GenAI
otel-gui
Langfuse
Phoenix
Braintrust
DeepEval
Ragas
Prometheus
Grafana
Harness AI telemetry signals
OpenAI trace grading / agent evals
```

AI infrastructure / operations:

```text
Argo CD
KEDA
MLflow
Kubeflow
vLLM
Triton
TensorRT-LLM
NVIDIA Dynamo
Docker MCP Toolkit examples
```

Sandboxing:

```text
E2B
Daytona
Modal
Cloudflare Sandbox SDK
Firecracker
gVisor
Kata
```

## Low-Trust Provider Tier

Free or unofficial model/API routers and CodexSaver-style delegation can help
free users and slow background enhancement, but they are low-trust providers.

Allowed:

```text
public-source summarization
draft enhancement
background candidate generation
cheap exploratory research
free-user slow queue
```

Blocked:

```text
private customer data
policy decisions
final verification
regulated context
sensitive source-handle expansion
certified context receipts
```

Required metadata:

```json
{
  "provider_tier": "free_best_effort",
  "trust_level": "low",
  "requires_reverification": true
}
```

## Research Signals From 2026

Current platform and research signals reinforce Baltor's direction:

- Microsoft Foundry is formalizing agent identities, hosted-agent permissions,
  RBAC, and agent lifecycle concepts.
- Harness is extending DevOps pipelines with AI DevOps Agents and autonomous
  agents for CI/CD, code review, CD remediation, and feature flag cleanup.
- GitHub and LangChain are normalizing portable agent skills.
- OpenAI is exposing agent evals, trace grading, and guardrails as platform
  primitives.
- Research on AI agents touching CI/CD and AI bot footprints in GitHub Actions
  points to the need for CI/CD safeguards around agent-driven changes.
- SWE-Skills-Bench and atomic-skill research reinforce the need to evaluate
  whether skills actually improve real software engineering outcomes.

The takeaway:

```text
Agent platforms are converging on CI/CD for agents.
Baltor should be the CI/CD layer for context and the governed release pipeline
for the backend agents that produce that context.
```

## Next Documentation Priorities

The next useful docs to create:

```text
1. Baltor Context Blueprint Schema
2. Baltor Context Receipt Schema
3. Baltor Agent/Tool Creation Provenance Schema
4. Baltor Skill Registry And Governance Standard
5. Baltor Context Wizard Release Checklist
6. Baltor Provider Tier Policy
7. Baltor Stage Page Content Guide
```

## Source Links

- Microsoft agents platform: <https://developer.microsoft.com/en-us/agents>
- Microsoft Foundry agent identity: <https://learn.microsoft.com/en-za/azure/ai-foundry/agents/concepts/agent-identity>
- Microsoft Foundry hosted agent permissions: <https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agent-permissions>
- Harness AI DevOps Agent: <https://developer.harness.io/docs/platform/harness-ai/devops-agent>
- Harness Agents: <https://www.harness.io/products/harness-ai/agents>
- GitHub agent skills: <https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-skills>
- LangChain Skills: <https://www.langchain.com/blog/langchain-skills>
- OpenAI agent evals: <https://platform.openai.com/docs/guides/agent-evals>
- OpenAI trace grading: <https://platform.openai.com/docs/guides/trace-grading>
- OpenAI Guardrails: <https://guardrails.openai.com/>
- SWE-Skills-Bench: <https://arxiv.org/abs/2603.15401>
- Scaling Coding Agents via Atomic Skills: <https://arxiv.org/abs/2604.05013>
- When AI Agents Touch CI/CD Configurations: <https://arxiv.org/abs/2601.17413>
- Reliability of AI Bots Footprints in GitHub Actions CI/CD Workflows: <https://arxiv.org/abs/2604.18334>
