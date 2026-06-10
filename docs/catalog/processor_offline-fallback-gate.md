# Offline fallback gate (connectivity check → local Knowledge Corpus)

*processor* · `processor/offline-fallback-gate` · v0.1.0 · experimental

If-Statement / gate processor: checks network connectivity (DNS probe +
optional latency ping) and, when offline, rewrites the pipeline step to
consume a local Knowledge Corpus instead of making a cloud API call.
Emits a gate_decision (offline | online) so downstream processors and
audit logs know which branch executed.

CAPABILITY LIFT (structural): this is the architectural gate that makes
any pipeline offline-capable. Without it, connectivity loss silently
fails the whole pipeline. The gate enforces an explicit, verifiable
branch rather than letting a timeout propagate. lift_reason:
no_addressable_source (cloud endpoint unavailable when gate fires);
deterministic_guarantee (the decision is a deterministic connectivity
check, not an LLM sample).

| axis | value |
|---|---|
| industry | ai, education, healthcare.public_health, cross_industry |
| capability | routing, safety_gating, governance |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| license | Apache-2.0 |



