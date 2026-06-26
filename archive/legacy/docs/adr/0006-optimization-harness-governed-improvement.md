# ADR 0006 — Optimization Harness: governed improvement, not silent speed

## Status

Accepted (C43). Follows ADR 0005 (Verification Gate). Optimization is permitted only after the gate exists; it
consumes only gate-`allow` artifacts.

## Context

After Enhancement and the Verification Gate, Baltor must improve cost / latency / size / ranking / routing of
context. The risk is an optimizer that "improves" a metric while changing truth: dropping an answer-critical
fact, leaving a contradictory claim in the pack, promoting an allegation, leaking tenant-private data, or
stripping the source handles that make a fact verifiable. "Smaller / faster / cheaper" is necessary, never
sufficient. We also want **multiple variations** of optimization that are **easily wrapped and chained**, not
one monolithic stage — and any external optimizer dependency (e.g. a prompt-compression library) must be
governed like every other provider.

## Decision

Build an `OptimizationHarness` (`scripts/runtime/optimization.py`, a declared runtime owner) with a suite of
optimizers behind ONE contract — `optimize(pack, signals) -> pack` — so they compose via `chain(...)`. Shipped:
`DedupeOptimizer`, `ExcludeHeldOutOptimizer`, `AuthorityRankOptimizer`, `CompressionOptimizer` (behind a
`CompressionProvider` seam; LLMLingua cataloged as the candidate primary, a deterministic stdlib stub wired).

The harness runs a candidate against a `BaselineSnapshot`, computes a `MetricBundle`, runs a `RegressionGate`
(answer facts preserved · source handles preserved · no held-out/allegation promoted · no tenant leak · nothing
fabricated), and **promotes only on measured lift + zero regressions**, emitting a content-addressed
`OptimizationReceipt` (schema `OptimizationReceipt.v1`, registered). It never overwrites the live pipeline:
optimization produces a candidate that must earn promotion.

## Consequences

- Optimization is provably safe: a candidate that loses truth is rejected even if it shrinks the pack.
- "Multiple variations, easily wrapped/chained" is real: every optimizer is the same contract; `chain()` composes them.
- The compression dependency is governed (catalog slot `compression`); no SDK lands without a card.
- Sets up **Consumption**: serve the optimized + verified + receipted pack with lineage and freshness.
- Determinism preserved: token estimates from string length, receipt ids content-addressed, time injected.

## Enforcement proofs

`check_optimization_harness` (wrappable + chainable suite; measured lift; regression gate promotes safe
improvements and blocks answer-fact loss / held-out promotion; deterministic schema-valid receipts; compression
cataloged) — registered in `scripts/baltor_flywheel.py`. Ownership by `check_runtime_ownership_manifest` +
`check_no_duplicate_runtime`; receipt type by `check_contract_registry_manifest`; the compression slot by the
C35 catalog proofs.
