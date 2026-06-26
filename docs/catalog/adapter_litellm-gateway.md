# LiteLLM gateway (routing backend candidate)

*adapter* · `adapter/litellm-gateway` · v0.1.0 · experimental

Wraps LiteLLM (YC W23, the de-facto OSS LLM gateway: 100+
providers behind an OpenAI-compatible surface) as a ROUTING BACKEND
candidate behind the Teleon inference port. OIPS keeps receipts, policy,
and allowed-use enforcement; LiteLLM supplies provider fan-out and
fallbacks. Never a second source of routing truth — the provider graph
stays canonical in architecture/model_provider_graph.json.
WRAP CANDIDATE (discovery ≠ trust): admitted from the 2026-06 YC/tool
landscape research as a governed CANDIDATE behind a port — its output is
never served as truth, it is sandboxed, and measured lift is PENDING
(two-axis gate: lift AND structural durability) before any promotion.
Landscape record: archive/legacy/docs/strategy/yc-context-landscape-2026-06.md.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | routing, serving |
| modality | text |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



