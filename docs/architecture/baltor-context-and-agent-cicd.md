# Baltor Context And Agent CI/CD

Date: 2026-06-03

Baltor should be framed as **CI/CD for enterprise context**. The same release
discipline used for software and agent platforms should apply to the context
those systems consume: builds, tests, promotion gates, receipts, rollback,
monitoring, and drift detection.

There are two related CI/CD systems:

```text
1. Context CI/CD
   The pipeline that turns raw organizational knowledge into verified,
   source-linked, policy-safe context packs.

2. Context Wizard / backend-agent CI/CD
   The pipeline that builds, tests, deploys, monitors, and rolls back the
   agents and workers that run Baltor's backend.
```

Microsoft's recent agent-platform direction is a useful reference point:
agents get deployment workflows, identity, permissions, evaluation, monitoring,
and lifecycle management. Baltor should apply the same pattern to context and
to the Context Wizards that operate the context supply chain.

## Product Boundary

Microsoft Foundry-style agent platforms govern the lifecycle of agents.

Baltor governs the lifecycle of context:

```text
Microsoft Foundry CI/CD = lifecycle for agents
Baltor Context CI/CD = lifecycle for verified context
Baltor Wizard CI/CD = lifecycle for the backend agents that produce context
```

Baltor should not become a generic agent builder. It should become the release
pipeline and assurance layer for context artifacts.

## Context CI/CD

Every context artifact should move through a pipeline:

```text
source event
-> context snapshot
-> parse
-> normalize
-> source-handle validation
-> ACL snapshot
-> prompt-injection / secret scan
-> claim extraction
-> reconciliation
-> anti-fragility check
-> enhancement
-> verification and adversarial validation
-> context evals
-> optimization / compression
-> context receipt
-> publish context pack
-> monitor drift
```

This is the direct analogy to software CI/CD.

| Software CI/CD | Baltor Context CI/CD |
|---|---|
| Source commit | Source-system change |
| Build artifact | Context object / context pack |
| Unit tests | Source-handle validation |
| Integration tests | Cross-source reconciliation |
| Security scan | Prompt-injection, secret, ACL, and policy scan |
| Test failure | Contradiction, stale source, missing evidence, or policy denial |
| Release gate | Human steward review |
| Deployment | Served context pack |
| Deployment receipt | Context receipt |
| Production monitoring | Drift monitor and freshness monitor |

## Context Artifact States

Context should have explicit promotion states:

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

These states make it clear that Baltor does not treat raw or generated text as
truth. Every claim and pack has a lifecycle.

## Context Blueprints

Baltor should define reusable context pack blueprints, similar to how agent
platforms define reusable deployment or identity patterns.

```text
implementation_pack_blueprint
review_pack_blueprint
incident_pack_blueprint
architecture_pack_blueprint
security_triage_pack_blueprint
support_pack_blueprint
api_context_pack_blueprint
repo_context_pack_blueprint
```

Each blueprint should define:

```text
required source types
required verification level
allowed provider tiers
required evals
token budget
freshness / TTL policy
policy checks
receipt fields
human review threshold
consumer contract
```

## Context Evals

Before a pack is published, run context-specific checks:

```text
source recall
source-handle validity
claim citation coverage
source freshness
contradiction detection
source precedence correctness
ACL correctness
prompt-injection risk
secret leakage risk
policy decision correctness
raw expansion safety
token budget
task usefulness
receipt completeness
```

Normal RAG evals are not sufficient. A generated answer can be faithful to
retrieved context while the retrieved context itself is stale, unauthorized, or
wrong.

## Context Receipts

Every served pack should emit a receipt:

```json
{
  "pack_id": "...",
  "pack_blueprint": "implementation_pack_blueprint",
  "subject": "...",
  "user": "...",
  "consumer": "Claude Code",
  "task_type": "implementation",
  "sources_used": [],
  "claims_included": [],
  "claims_excluded": [],
  "conflicts_disclosed": [],
  "policy_decision": "...",
  "verification_level": "...",
  "ttl": "...",
  "retrieval_policy": "...",
  "reranker": "...",
  "compressor": "...",
  "worker_trace_id": "...",
  "context_trace_id": "..."
}
```

The receipt is the context equivalent of a build artifact plus deployment log.

## Context Wizard / Backend-Agent CI/CD

Context Wizards are the agents/workers that operate Baltor's backend:

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

These workers need their own CI/CD because they affect the quality and safety of
served context.

## Agent / Tool Creation Provenance

Every new agent, bot, worker, tool, skill, command, parser, scanner, connector,
or MCP server should have provenance for the **decision to create it**, not only
for the source code that implements it.

Baltor should be able to answer:

```text
Who requested this agent/tool?
When was it requested?
Where did the request originate?
Why was it needed?
What alternatives were considered?
How was the build decision made?
Which agent, worker, user, or policy approved it?
Which sources/evidence justified it?
Which risks were identified?
Which context packs, incidents, tickets, or eval failures led to it?
```

This is a core CI/CD rule. A Context Wizard should not appear because an agent
spontaneously decided to build one. It should be created through a documented
request, decision, approval, and release path.

Creation provenance should be recorded as a first-class artifact:

```json
{
  "creation_record_id": "agent_creation_...",
  "artifact_type": "context_wizard | tool | bot | skill | command | mcp_server",
  "artifact_name": "billing_retry_conflict_hunter",
  "requested_by": {
    "type": "human | agent | policy | incident | eval_failure",
    "id": "..."
  },
  "request_origin": {
    "source": "jira | incident | context_drift_report | eval_dashboard | steward_console",
    "source_handle": "ctx://..."
  },
  "created_at": "...",
  "why": "...",
  "problem_statement": "...",
  "decision_summary": "...",
  "alternatives_considered": [],
  "approver": "...",
  "approval_policy": "...",
  "risk_classification": "low | medium | high | regulated",
  "allowed_sources": [],
  "allowed_tools": [],
  "blocked_actions": [],
  "required_evals": [],
  "release_gate": "...",
  "lineage": {
    "context_pack_ids": [],
    "incident_ids": [],
    "eval_run_ids": [],
    "worker_run_ids": []
  }
}
```

The creation record should be linked to:

```text
source repository commit
prompt / instruction version
skill package version
tool manifest hash
MCP manifest hash
policy version
eval suite version
deployment id
context receipts affected by the artifact
```

## Meta-Skill Generated Agents

Tools like RevFactory Harness and GStack are useful because they package or
generate agent teams, skills, commands, and workflow discipline. Baltor should
use that pattern for Context Wizard creation, but generated agents still need
creation provenance.

If a meta-skill generates a new worker team, record:

```text
generator tool
generator version
input prompt/request
source handles used by the generator
generated agents
generated skills
generated commands
reviewer or steward approval
changes made after generation
test results
release decision
```

Generated workers should default to `draft` until they pass release gates.

## Wizard Artifact Types

Each worker should be versioned as a deployable artifact:

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

The important rule: a worker is not just code. Its prompts, models, tools,
schemas, evals, and policies are part of the release.

## Wizard CI/CD Pipeline

Every Context Wizard release should run:

```text
lint / static checks
schema validation
prompt/instruction scan
tool allowlist validation
MCP manifest scan
secret scan
unit fixtures
reference context-pack regression tests
source-handle validation tests
policy-denial tests
adversarial prompt-injection tests
cost/latency budget tests
canary run
human approval when risk threshold is high
deployment
post-deploy monitoring
rollback if evals or production metrics regress
```

This is especially important for model-backed workers. A small prompt or model
change can change which claims are extracted, which conflicts are noticed, and
which context gets served.

## Wizard Release Metadata

Every worker run should record:

```json
{
  "worker_id": "claim_extractor",
  "worker_version": "1.4.2",
  "prompt_version": "claim_extractor_prompt_2026_06_03",
  "model_policy": "cheap_first_risk_escalation_v2",
  "tool_policy": "source_read_only_v1",
  "input_schema": "candidate_claim_input_v1",
  "output_schema": "context_claim_v1",
  "eval_suite": "claim_extraction_regression_v3",
  "deployment_id": "...",
  "trace_id": "..."
}
```

Context receipts should be able to reference these worker versions.

## Agent Identity And Permissions

Microsoft's agent identity direction is useful for Baltor. Baltor should define
identities for backend workers and Context Wizards:

```text
worker identity
allowed source systems
allowed source handles
allowed raw expansion scope
allowed write actions
allowed model provider tiers
allowed retention policy
approval requirements
```

No worker should receive broad access by default. Access should be scoped by
task, source, tenant, environment, and risk.

## Environments

Use explicit environments for both context and workers:

```text
local
dev
staging
canary
production
regulated / enclave
```

Context packs should also carry environment labels:

```text
generated_in
valid_for
source_environment
consumer_environment
```

This avoids serving dev/staging context into production tasks or leaking
production-only context into local experiments.

## Rollback

Rollback has two dimensions:

```text
1. Worker rollback
   Revert a Context Wizard release, prompt version, tool policy, or model route.

2. Context rollback
   Revoke or supersede context packs and claims that were produced by a bad
   worker release.
```

If a worker regression is found, Baltor must be able to answer:

```text
Which packs did this worker version generate?
Which claims did it promote?
Which consumers received those packs?
Which receipts reference this worker?
Which claims or packs must be revalidated?
```

## Observability

Track both context quality and worker health.

Context signals:

```text
pack published
pack served
source handle expanded
claim verified
claim rejected
conflict detected
source stale
policy denied
receipt issued
context drift detected
```

Worker signals:

```text
worker run started
worker run completed
worker run failed
retry count
queue depth
latency
cost
model provider
tool calls
eval score
policy decision
human review rate
rollback event
```

Use OpenTelemetry/GenAI conventions where possible, but define Baltor-specific
event names for context artifacts.

## Low-Trust Provider Gate

Free or unofficial model/API providers can be useful for slow background work
and free-user enhancement, but they must be excluded from certified flows unless
their output is reverified.

```text
free_best_effort
  allowed: draft enhancement, public-source summarization, background research
  blocked: private sources, policy, final verification, regulated contexts
```

Context CI/CD should enforce this provider tier before publish.

## Implementation Path

### Phase 1: MVP CI/CD

```text
Postgres context registry
Pydantic AI typed workers
DBOS or Inngest for durable-ish worker execution
Langfuse/Phoenix for traces
DeepEval/Ragas/custom eval fixtures
Context receipt schema
basic worker version metadata
```

Deliver:

```text
context_for_ticket()
verify_claim()
context_receipt()
worker_trace()
```

### Phase 2: Production Worker CI/CD

```text
Temporal or Restate
OpenTelemetry events
policy hooks with OpenFGA/OPA
MCP manifest scanning
reference pack regression suite
canary deployment
worker rollback
context pack revocation/revalidation
```

Deliver:

```text
worker release pipeline
context pack promotion gates
drift monitor
context artifact rollback report
```

### Phase 3: Enterprise / Microsoft-Aligned Deployment

```text
agent/workflow identity model
RBAC/ABAC/ReBAC permissions
Azure Monitor / Datadog / Grafana integration
Microsoft Foundry / Azure AI Foundry interoperability
Cloudflare / Context Forge / Portkey MCP gateway integration
regulated enclave deployment
```

Deliver:

```text
context CI/CD control plane
context steward console
enterprise audit exports
regulated deployment profile
```

## Positioning

Use this framing:

> Baltor is CI/CD for enterprise context.

Longer:

> Agents are becoming deployable software. Context needs the same release
> discipline: builds, tests, promotion gates, receipts, rollback, and
> monitoring. Baltor provides that CI/CD layer for organizational knowledge.

When positioning alongside Microsoft:

> Microsoft Foundry helps enterprises build, deploy, and govern agents. Baltor
> helps those agents receive verified, current, policy-safe context through a
> CI/CD pipeline for organizational knowledge.

## Source Links

- Microsoft agents platform: <https://developer.microsoft.com/en-us/agents>
- Azure AI Foundry agent identity: <https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/agent-identity>
- Deploy hosted agents with Azure AI Foundry: <https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/deploy-hosted-agent>
- Hosted agent permissions: <https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agent-permissions>
