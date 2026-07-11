# `tools/` — reference implementations of the standards

These are **working reference implementations** of the two headline standards, copied from the reference
project. They are meant to be **adapted per project**, not run as-is — the *mechanism* is generic, only the
project-specific bindings change.

| File | Implements | What to adapt |
|---|---|---|
| `example_portfolio_config.py` | [`../standards/MULTI-PATH-DEVELOPMENT.md`](../standards/MULTI-PATH-DEVELOPMENT.md) | Every runtime decision point is a portfolio of contract-substitutable paths behind one selector, with an `ACTIVE_DEFAULT` that reproduces current behavior and disclosed `DecisionReceipt`s. **Adapt** `DECISION_POINTS` / the resolver callables / `PARAMETERS` to your systems. |
| `example_quality_ratchet.py` | [`../standards/VERIFY-THE-VERIFIER.md`](../standards/VERIFY-THE-VERIFIER.md) | Headline metrics recorded as candidate floors **from computed manifests** (never hand-typed); a silent regression below a floor is a hard failure; unsupplied external metrics are gaps, not fake passes. **Adapt** `METRIC_SPECS` to your project's headline numbers. |

Both carry a self-contained `--self-test` that proves the mechanism has teeth (the ratchet catches a
simulated regression; the portfolio's paths are substitutable and planned paths raise rather than silently
no-op). Wire your adapted versions into an umbrella `run_proofs` entrypoint (see
[`../standards/VERIFY-THE-VERIFIER.md`](../standards/VERIFY-THE-VERIFIER.md)).

The two other pieces of reusable machinery worth porting (kept in the reference project, not copied here to
avoid dead imports): the **`run_parallel`** comparator (runs every path on the identical input, records
per-path receipts, never serves a candidate as truth) and a **path bake-off** that races the portfolio and
emits a per-task-class leaderboard. See `MULTI-PATH-DEVELOPMENT.md` for how they fit together.

## Portable org tools (multi-repo, driven by `../contracts/surface-registry.json`)

Two additional runnable tools operate on the single-source **surface registry** rather than the headline
standards — they keep a growing multi-repo org in sync without any repo reading through another's source.
Both are offline, deterministic, and carry a `--self-test`; the `skills/` (`check-organization`,
`organize-and-refresh`, `split-repo`) drive them.

| File | What it does |
|---|---|
| `check_cross_repo_dependency_law.py` | Portable CI gate that proves the cross-repo dependency boundary from `../contracts/surface-registry.json`: every declared `may_depend_on` edge points at a real surface and is not a forbidden edge, the graph is acyclic, and each declared consumed surface is actually allowed. The multi-repo generalization of the reference project's `scripts/check_portfolio_dependency_law.py`. |
| `generate_repo_edges.py` | The edge-graph generator: turns the surface registry + each surface's published `exposes` into per-repo edge digests (`<surface>.edges.json` + `<surface>.EDGES.md`) and the global dependency graph (`graph.json` + `GRAPH.md`, a mermaid diagram + adjacency list) under `../generated-edges/`. Reads contracts only, never any repo's source, so cross-repo awareness stays in sync while internals stay private. |
