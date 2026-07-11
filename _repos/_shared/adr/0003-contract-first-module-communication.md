# ADR 0003 — Contract-First Module Communication

## Status
Accepted (C33; builds on C32 runtime contracts).

## Context
Every module talking its own JSON shape, log keys, and error behavior is contract drift. C32 introduced the
five versioned envelopes + JSON-Schema validation + structured logs; this ADR makes them a governance rule.

## Decision
No command/event/artifact/processor/pipeline/queue/log type may be introduced without a
`architecture/contract_registry.json` entry (name + version + owner + status + schema where applicable).
Every inter-module payload is a versioned envelope validated against a schema; events are CloudEvents-shaped;
HTTP/queue contracts are documented in OpenAPI/AsyncAPI; logs use OpenTelemetry-style attributes. The
dashboard is a projection — it never owns truth.

## Consequences
New contracts are discoverable + validated; unregistered types fail the build; consumers can rely on stable
outside surfaces while module internals evolve.

## Enforcement proofs
`check_contract_registry_manifest` · `check_runtime_schema_validation` · `check_architecture_dashboard_projection_only`.
