# Architecture Drift Guardrails (C33)

Drift is now measurable and FAILING, not documented-and-ignored. Each drift type is a separate failure mode
with a guardrail proof in the flywheel:

| Drift type | Symptom | Guardrail proof |
|---|---|---|
| Architecture | modules bypass runtime / call server globals / make a 2nd bus | `check_import_boundaries_manifest`, `check_no_direct_provider_bypass` |
| File organization | everything piles into scripts/, vague names, random folders | `check_file_layout_policy`, `check_project_spine_folders` |
| Monolith | 800+-line files mixing CLI/storage/logic | `check_monolith_allowlist` (budgets + allowlist w/ split targets) |
| Contract | each module invents its own JSON shape | `check_contract_registry_manifest`, `check_runtime_schema_validation` |
| Runtime | duplicate store/bus/registry/gateway/harness | `check_no_duplicate_runtime`, `check_runtime_ownership_manifest` |
| Logging | random keys, no correlation ids | `check_structured_runtime_logging` |
| Dashboard truth | UI computes/stores truth or leaks private intel | `check_architecture_dashboard_projection_only` |
| Security | secrets/private data in code/logs/UI | `check_llm_secret_hygiene`, `check_no_direct_provider_bypass` |
| Decision | docs say one thing, code another | `check_architecture_adr_coverage` |

## Definition of Done (every future pass)
A pass is green only if: its feature proof passes **and** the architecture boundary/file-layout/contract-
registry/module-size proofs pass (or debt is allowlisted), no new domain logic appears in runtime core, no
new unregistered processor/queue/event/artifact type appears, the dashboard stays projection-only, logs are
structured + correlated, and an ADR is added if a boundary/storage/runtime/security decision changed.

## Standards stack
JSON Schema (payloads) · CloudEvents (events) · OpenAPI (HTTP) · AsyncAPI (queues) · OpenTelemetry-style
log/trace naming · ADRs (durable decisions). Internal contracts are not arbitrary; they reuse these.
