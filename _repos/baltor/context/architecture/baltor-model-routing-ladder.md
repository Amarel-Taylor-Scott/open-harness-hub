# Baltor Model Routing Ladder

Updated: 2026-06-01

Baltor model routing is provider-neutral. Model names and vendors are examples
inside capability slots, not routing rules. The durable decision is:

```text
task + risk + uncertainty + cost + privacy + evidence policy
  -> capability slot
  -> concrete model adapter available at runtime
```

Do not escalate by brand or prestige. Escalate by risk.

## Capability Slots

| Tier | Slot | Example families | Primary use |
| --- | --- | --- | --- |
| 0 | `deterministic` | regex, date parsers, JSON Schema, Pydantic, SHACL, entity linkers | Normalize, validate, dedupe, parse, enforce schema. |
| 1 | `small_local` | Gemma-small, Qwen-small, Granite-small, Ministral, Nemotron-small | Bulk tags, simple claims, ambiguity and fragile-fact flags. |
| 2 | `mid_open` | Qwen-mid, Gemma-mid, Mistral Small/Medium, GLM Flash/Air | Evidence review, edge extraction, schema repair, summary verification. |
| 3 | `large_open` | MiniMax, Kimi, DeepSeek, Llama, Mistral Large, GLM, Nemotron, Jamba | Hard reasoning, long-context review, graph enrichment, conflicts. |
| 4 | `ensemble` | Mixed independent models and rubrics | Disagreement resolution and uncertainty estimation. |
| 5 | `frontier` | Current frontier APIs behind policy | Appeals for high-stakes or unresolved claims. |
| 6 | `human_review` | Analyst, SME, legal, compliance, security, clinical | Final approval for unresolved high-risk context. |

## Escalation Score

The default score is:

```text
0.20 * uncertainty
+ 0.20 * conflict
+ 0.15 * downstream_risk
+ 0.15 * graph_centrality
+ 0.10 * temporal_fragility
+ 0.10 * ambiguity
+ 0.05 * low_source_quality
+ 0.05 * model_disagreement
```

Thresholds:

| Score | Route |
| --- | --- |
| 0.00-0.30 | `deterministic_then_small_local` |
| 0.31-0.55 | `mid_open` |
| 0.56-0.75 | `large_open` |
| 0.76-0.90 | `ensemble_then_frontier_if_needed` |
| 0.91-1.00 | `frontier_then_human` |

## Product Contracts

- HTTP: `/api/context-gateway/model-routing`
- MCP: `context_model_routing`
- Schemas:
  - `_repos/shared-backend-components/schemas/context-model-profile.schema.json`
  - `_repos/shared-backend-components/schemas/context-model-routing-policy.schema.json`
- Postgres:
  - `context_model_profile`
  - `context_model_routing_policy`
  - `model_route_decision`

The endpoint returns example model families in capability slots and a sample
route decision for the latest run. The concrete runtime adapter remains
replaceable.
