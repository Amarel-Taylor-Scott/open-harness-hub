# Recursive encoded payload triage

*pipeline* · `pipeline/recursive-encoded-payload-triage` · v0.1.0 · experimental

Pre-LLM guardrail pipeline that recursively sanitizes encoded spans, routes checks through an edge micro-model, and escalates uncertain or high-risk decoded content.

| axis | value |
|---|---|
| industry | ai, security.defensive, media, cross_industry |
| capability | safety_gating, classification, routing, evaluation |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Decide whether a prompt or tool request containing possible encoded spans can be safely routed to an edge AI model.

**pipeline_kind:** `edge_ai.recursive_encoded_payload_triage`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `sanitize-encoded-spans` | tool | `tool/recursive-encoding-sanitizer` | - |
| 2 | `route-edge-authorization` | tool | `tool/edge-micro-model-authorization-router` | - |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | - |

