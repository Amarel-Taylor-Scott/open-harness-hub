# ADR 0007 — Primitive store (git-like + content-addressed + scoped) & the generic executor

## Status
Accepted (2026-07-04) as a **reference implementation + evaluation** (candidate in `experiments/`), not yet a
promoted `src/` module.

## Context
Owner: implement Omnigraph **plus our rules** for storing primitives across a database, a git-like environment
(forks / parallel versions / merges) and buckets; treat **every one of our repos as a group of internal
primitives/systems** — stored/versioned like external primitives but **secret** (excluded from public search
& use); and add a **generic stateless executor** that "captures inputs and outputs and where to download the
code from git." Assessed reuse-first: `LineageBundle`/`PromotionRecord` already model fork/remix/supersede +
the `scope` (`global_public`/`tenant_private`) secrecy law; Omnigraph productizes the branchable object-store
graph.

## Decision
Build `experiments/primitive_store/primitive_store.py` (18 self-test checks, deterministic) encoding:
1. **Three planes** joined by the content hash — content bucket (bodies/code) · git-like `LineageGraph`
   (fork/branch/merge/supersede, prior versions KEPT) · scope-tagged search index (rebuildable projection).
2. **Scope = our code is a secret primitive.** `PUBLIC` vs `INTERNAL`; internal is never returned by a public
   search and never run for a public caller. Every repo = a `system` of internal primitives. Reuses the
   `LineageBundle.scope` "tenant_private never global" law.
3. **Candidate/truth** — writes born candidate; `promote()` requires a rollback target; prod runs only promoted.
4. **Multi-path port** — `LocalPrimitiveStore` (reference / bake-off baseline) + `OmnigraphPrimitiveStore`
   (candidate adapter, real endpoints, raises loudly without an instance) behind one selector. Omnigraph is a
   backend to **race**, not a hardwired dependency.
5. **Generic executor** — one stateless runner: resolve → enforce scope + promotion state → fetch code **by
   content ref** (cached) → pluggable sandbox runner → validate typed I/O → receipt. Realizes "one generic
   image, fetch the primitive by ref"; extends the hosting plan's reversibility to its endpoint.

## Consequences
The primitive-storage + generic-execution model is concrete and tested; our own code becomes internal (secret)
primitives in the same store; Omnigraph has a clean seam to bake off. Prior art grounds it (Deno Deploy from
URL, Nix content-addressing, Lambda, Omnigraph versioned code). **Production wiring pending:** `canonical_id`
single-source, real object bucket via the credential-plane, the real sandbox runner (not `exec`), a real
Omnigraph client, pyprefix pass + `run_proofs` wiring before promotion into `src/`.

## Enforcement / links
`schemas/distillation/LineageBundle` + `PromotionRecord` (lineage/promotion parity); `governance/
AccountabilityBinding` (the primitive's owner); the registry port; ADR 0006 (Omnigraph evaluation).
