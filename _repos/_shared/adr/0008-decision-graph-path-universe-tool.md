# ADR 0008 — A decision-graph / path-universe tool (Multi-Path Development, made a product)

## Status
Accepted-in-principle (2026-07-04, owner-raised). Recommend build as a focused library repo; scaffolding gated
on the owner's go.

## Context
Owner proposes a repo/project that **graphs development decisions, generates the full universe of potential
paths, highlights the supported/tested/chosen path(s), and encourages abstraction/wrappers/ports so new paths
are trivial to add, toggle on/off, and test** — citing ML-competition systems (Kaggle) that build a config
grid over preprocessing × model × params × post-processing. Assessed reuse-first.

## Decision
1. **This is our Multi-Path Development law, made a first-class developer-facing tool — the ENGINE already
   exists.** Do NOT rebuild it: `parallel_paths.run_parallel` + the `DescentAttempt` ledger,
   `run_path_bakeoff`, and `primitive_paths_config` already race contract-substitutable paths on the same
   input and keep losers as labelled fallbacks. Build the tool ON TOP:
   - **decision registry** — each decision node = a named option-set (the config grid).
   - **path-universe generator** — the constrained Cartesian product of option-sets (with feasibility rules,
     so it doesn't explode) → the "full universe of paths."
   - **markers** — `tested / chosen / candidate / rejected` per path, reusing the candidate/truth boundary +
     the `primitive_store` lineage graph (a path IS a branch/variation in the DAG).
   - **toggles** — turn a path on/off (feature-flag style) without a code change.
   - **selector + bake-off** — the existing engine picks the optimal and serves it; the graph shows why.
2. **Prior art / the ML analogy is exact:** Hydra (config composition + multirun), Optuna / W&B sweeps,
   sklearn `Pipeline` + `GridSearchCV`, Kaggle config-grid notebooks, feature flags (LaunchDarkly). Same
   shape — a grid over the whole pipeline, one selector, the winner served, the losers kept.
3. **Abstraction discipline it enforces = our existing law:** every decision point is a portfolio behind a
   selector (a port/wrapper), never an `if`. The tool makes that portfolio **visible and toggleable** — and
   the decision-graph in the primitive-factory architecture artifact (§09) is exactly its hand-drawn output.
4. **Home (recommendation):** a new **library** repo `aidoneright-decision-graph` (layer=library), consumed by
   the substrate and every product through a port — it graphs decisions for OUR code (internal primitives) AND
   is a candidate product surface. Alternative: an OpenHubForAI capability. Register it in the surface-registry.

## Consequences
Multi-path stops being only a law and becomes tooled + visible; new paths become trivial to add/test/toggle;
the decision graph is generated, not hand-authored. Reuses the parallel_paths engine + the primitive_store
lineage; no engine rebuilt.

## Enforcement / links
`standards/MULTI-PATH-DEVELOPMENT.md`; `parallel_paths` / `run_path_bakeoff` / `primitive_paths_config`;
`experiments/primitive_store` (paths = branches/variations); ADR 0006–0007.
