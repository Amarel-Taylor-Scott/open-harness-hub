# Primitive Cloud Guardrail Runtime Handoff

Last updated: 2026-07-01

Audience: Claude 5 Fable, Codex, Claude Code, and model lanes expanding
guardrail primitives for AI apps, agents, RAG, tool calls, and workflows.

Status: execution brief plus seed registry. These rows are candidate route and
deployment artifacts, not promoted truth.

## Core Positioning

Do not build this as a Bedrock-branded surface.

Build:

```text
cloud-agnostic deterministic guardrail primitives
  + provider adapters
  + policy backends
  + deployment wrappers
  + decision receipts
  = portable guardrail runtime
```

Bedrock-style guardrails, Google-style model protection, Azure-style content
safety, OPA/Cedar-style policy engines, and local deterministic policy engines
are adapters. The product is the primitive layer.

## Seed Pack

The concrete seed pack is:

```text
catalog/knowledge-packs/data/primitive-cloud-guardrail-runtime/
```

It contains:

- `guardrail_primitives.jsonl` for prompt, data-leak, RAG, tool-call, output,
  policy, and audit primitives;
- `guardrail_groups.jsonl` for composable gateways;
- `provider_adapters.jsonl` for cloud/provider and deterministic policy
  adapters;
- `deployment_wrappers.jsonl` for API gateway, serverless, container,
  Kubernetes, MCP prehook, queue worker, Envoy-style auth, and receipt
  collector shapes;
- `industry_guardrail_packs.jsonl` for practical vertical packs;
- `benchmark_fixtures.jsonl` for proof fixtures.

All rows stay:

```json
{
  "candidate": true,
  "serves_truth": false
}
```

until provider docs, policy behavior, runtime effects, fixture tests, and
decision receipts are verified.

## Product Shape

Core runtime:

```text
HTTP API
SDK middleware
policy bundle loader
decision engine
provider adapters
receipt emitter
OpenTelemetry-style exporter
CloudEvents-style audit event exporter
test harness
```

Primitive packs:

```text
prompt injection and jailbreak
PII, PHI, and secret redaction
RAG source, citation, and grounding
tool-call approval and side-effect gates
output claim, schema, and regulated-advice gates
policy-as-code gates
decision receipt and audit export
```

Cloud wrappers:

```text
API gateway middleware
FastAPI middleware
Express middleware
Lambda-style handler
Cloud Run-style container
Azure Functions-style function
Kubernetes sidecar
Knative service
Envoy external authorization service
MCP prehook
queue worker
receipt collector
```

## Sharp Wedge

The strongest first wedge is not generic content moderation. It is:

```text
deterministic guardrails for agent tool calls and cloud-deployed AI workflows
```

Agents need controls around:

```text
which tools can be called
with which arguments
under which user role
against which tenant or customer
with which external side effects
with which approval requirement
with which rollback or idempotency plan
with which audit receipt
```

That is exactly where primitive guardrails are stronger than a monolithic
moderation API.

## Example Group

```text
grp:agent.tool_call_guardrail_gateway
```

Visible edge:

```text
ProposedToolCall+UserContext+ToolPolicySet
  -> ToolCallDecision+GuardrailDecisionReceipt
```

Member primitives:

```text
guard:tool.schema_validate
guard:tool.allowlist_check
guard:tool.auth_scope_check
guard:tool.external_side_effect_gate
guard:tool.human_approval_required
guard:tool.rollback_plan_required
guard:audit.tool_call_receipt
```

This group should run as an MCP prehook, API gateway guard, queue worker guard,
serverless function, or Kubernetes sidecar without changing the core primitive
contract.

## Validation

Run:

```bash
python3 scripts/check_primitive_cloud_guardrail_runtime.py --self-test
python3 scripts/check_primitive_variation_dimension_atlas.py --self-test
python3 scripts/check_primitive_customization_overlays.py --self-test
python3 scripts/check_primitive_agent_graph_path_mixtures.py --self-test
```

For broader repo confidence, also run:

```bash
python3 scripts/check_handoff_docs_freshness.py --self-test
python3 scripts/check_ai_done_right_surface_family.py --self-test
python3 scripts/check_portfolio_dependency_law.py --self-test
```
