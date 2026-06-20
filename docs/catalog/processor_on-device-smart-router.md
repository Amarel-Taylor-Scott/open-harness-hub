# On-device smart inference router (offline-first, cost-adaptive)

*processor* · `processor/on-device-smart-router` · v0.1.0 · experimental

Selects the best available inference path for a given request by probing
connectivity, device capability, and latency budget before committing to a
model call. Priority order: on-device CPU (always available) → local GPU /
Ollama HTTP (LAN) → cloud API (only when connectivity confirmed and cost
ceiling not exceeded). Emits a signed routing decision so downstream
processors can log which path was used for cost accounting and replay.

CAPABILITY LIFT (structural): this lift is architectural — a bare model
call assumes a cloud endpoint is always reachable. The smart router is the
component that makes the whole pipeline portable to offline and constrained
environments. Without it, any connectivity loss silently fails the pipeline.
lift_reason: no_addressable_source (cloud path unavailable when offline);
deterministic_guarantee (routing policy is a verifiable rule, not a guess).
The router's offline-first preference cannot be replicated by prompting a
cloud model — the cloud model is what is being routed away from.

| axis | value |
|---|---|
| industry | ai, education, healthcare.public_health, cross_industry |
| capability | routing, classification, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | Apache-2.0 |



