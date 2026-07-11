# Shared Inference Gateway (internal)

Internal **LLM-plane console** — not a public domain. Object-level inference *preference* →
governed provider/model graph → `ModelInvocationReceipt`. Shows route decisions, free/limited
endpoint classification, quarantine of shared-key/bypass endpoints, and secret-*refs* (never
values). **Projection-only:** reads governed projections, owns no truth; LLM output is never truth.

## Open it
`Shared Inference Gateway.html` — built on the shared kit (`oh-*` tokens + primitives).

Feeds **OpenEndpointHub** (endpoint eligibility) and emits the **ModelInvocationReceipt** that
**OpenReceiptHub** catalogs. See `README.md` + `BACKEND-STACK.md`.
