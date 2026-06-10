# ADR 0002 — Runtime Ownership & No Duplicate Frameworks

## Status
Accepted (C33).

## Context
The biggest sprawl risk is reinventing core machinery — a second bus, queue, store, harness, registry, or
LLM gateway — each with its own contract. A `ProcessorRegistry` already existed in two places.

## Decision
Declare exactly one canonical owner per runtime concept in `architecture/runtime_ownership.json`
(DurableStore, EventBus, the five envelopes, ProcessorHarness, ProcessorRegistry, PipelineRunner,
LLMGateway, TenantStoreResolver, ArtifactLedger, RuntimeLogger, …). A duplicate framework class outside the
owner — or its explicit legacy allowlist — fails the build. The pre-existing duplicate
(`pipeline_runtime.ProcessorRegistry`) is allowlisted with a consolidation deadline.

## Consequences
No silent second framework can appear. Consolidation debt is explicit and dated.

## Enforcement proofs
`check_runtime_ownership_manifest` · `check_no_duplicate_runtime` · `check_scripts_are_entrypoints`.
