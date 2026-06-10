# ADR 0004 — External Capability Catalog & Repo Replaceability

## Status

Accepted (C35). Extends ADR 0001 (project spine), 0002 (runtime ownership), 0003 (contract-first).

## Context

Baltor uses many external repos as swappable infra (parsers, retrieval, claim-graph memory, durable workflow,
sandboxes, observability). Those repos decay — they get archived, relicensed, pivoted, or turn out to be
hallucinated entries in upstream "best tool" lists. The verified seed `data/backend-tools.yaml` (13 capability
keys + a `flagged:` do-not-reintroduce block) recorded *which* tools, but nothing in code enforced that:

- domain code depends on a capability, not a vendor;
- a new third-party dependency arrives with a card, contract, fallback, license, and health;
- a flagged tool (Synapse AI, Microsoft Conductor, Kuzu original, Neo4j GraphRAG, Marqo, Envoy-as-gateway)
  cannot quietly reappear;
- self-evolving multi-agent runtimes are kept as **foils**, not adopted (see
  `research/external-tools/self-evolving-coding-agents.md`).

The governed runtime is stdlib-only, so this is **pre-registration**: get the discipline in place before the
first real dependency, not after.

## Decision

Introduce the **External Capability Catalog** as three governed manifests —
`architecture/external_capability_catalog.json`, `repo_health_policy.json`, `repo_replacement_matrix.json` —
read by a single owner, `class CapabilityRegistry` in
`src/baltor/runtime/registry/capability_registry.py` (declared in `runtime_ownership.json`).

- Each **capability slot** mirrors a backend-tools.yaml key (or a research-earned slot) and carries: the wired
  adapter (a working stub), a candidate primary, fallbacks, an I/O contract + example, contract proofs,
  license, status, health.
- The 13 keys and the flagged names are **read from the YAML** (single source); catalog↔YAML drift fails a proof.
- Every adoptable slot ships a **stub** so the system runs with zero external deps; provider SDKs may only be
  imported inside an approved adapter path.

## Consequences

- Adding a real dependency is now a governed act: no card → no import (build fails).
- Replacing a decayed repo is a documented swap (matrix `swap_steps`) that keeps the contract + proofs.
- A flagged/decayed/archived tool cannot become an adopted adapter.
- Slight overhead: a new provider must be cataloged before use. That is the intended cost.

## Enforcement proofs

`check_external_capability_catalog`, `check_repo_health_policy`, `check_provider_replacement_matrix`,
`check_no_uncataloged_github_repos`, `check_no_direct_external_imports`, `check_capability_contract_examples`,
`check_flagged_tools_not_reintroduced` — all registered in `scripts/baltor_flywheel.py` PROOF_MODULES.
Ownership of `CapabilityRegistry` is enforced by `check_runtime_ownership_manifest` + `check_no_duplicate_runtime`.
