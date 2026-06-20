# ADR 0005 — Verification Gate & the Enhancement→Optimization Promotion Boundary

## Status

Accepted (C40). Extends ADR 0001–0004. Sequenced ahead of the Fact Watchtower (C41) and the Optimization
Harness (C43) — Optimization is not allowed to begin until this gate exists.

## Context

Baltor's stage ladder runs Source → Reconciliation → Anti-Fragility → Enhancement → Optimization →
Consumption, under a Verification rail. Enhancement *adds* value (enrichment, derived conclusions, model
signals). The danger is moving into Optimization (compression, retrieval ranking, routing, caching, batching)
**before** that value is verified — an optimizer would then happily make the wrong thing faster: rank or
compress contradictory material, promote an unverified allegation, serve a stale fact, or leak tenant-private
data into shared output. "It's faster / smaller / cheaper" is necessary, never sufficient.

The substrate to judge this already exists: governed artifact types
(`atomic_fact`/`narrative_allegation`/`conclusion`/`emotion_signal` with distinct governance), source handles
+ content hashes, deterministic conflict detection + authority reconciliation, and tenant isolation. What was
missing was an explicit, blocking, *reusable* decision point — not a story on the demo page.

## Decision

Introduce a **mandatory Verification Gate** between Enhancement and Optimization
(`scripts/runtime/verification_gate.py`, `class VerificationGate`, a declared runtime owner). For every
enhanced artifact it emits `allow` or `hold_out` plus a content-addressed `VerificationReceipt` (registered as
the `verification_receipt` artifact type, schema `VerificationReceipt.v1`) recording why. Optimizers consume
only `allow` artifacts; held-out items are retained as warnings, never as truth.

The gate is a **projection/decision** — it never mutates canonical state (promotion happens downstream), it
reads governance from the single artifact-type registry, and it is deterministic + offline (injected time,
content-addressed ids). The reconciler remains the conflict authority; the gate reads its verdict.

## Consequences

- "This artifact may enter Optimization / Consumption" becomes an explicit, receipted, auditable decision.
- Allegations, unresolved conflicts, stale fragile facts, unsupported conclusions, handle-less or hashless
  artifacts, tenant leaks, and ungrounded model output are blocked from promotion by default.
- Optimization (C43+) can be built safely on top: it improves cost/latency/compression/ranking/routing over an
  already-verified set, behind its own regression gate + promotion receipt.
- The fragile-fact dimension is graceful until the Fact Watchtower (C41) supplies freshness metadata.

## Enforcement proofs

`check_verification_gate` (allows a verified fact; holds out allegation / unresolved-conflict / stale-fragile /
no-source-handle / unsupported-conclusion / tenant-leak / ungrounded-model; deterministic schema-valid
receipts; projection-only) — registered in `scripts/baltor_flywheel.py` PROOF_MODULES. Ownership enforced by
`check_runtime_ownership_manifest` + `check_no_duplicate_runtime`; the receipt type by
`check_contract_registry_manifest`.
