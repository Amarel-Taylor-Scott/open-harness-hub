# ADR 0012 — "VariantGraph" is the existing multi-path engine; do not build a duplicate repo

## Status
Accepted (2026-07-04, owner-directed: "make sure we aren't inventing duplicate repositories/graphs/
functions — we already have some of this functionality; integrate it into the surfaces or backend tools").

## Context
The owner proposed **VariantGraph** — a framework where alternative implementations/strategies/paths are
first-class objects and a runtime policy selects the path by constraints/context/telemetry/outcomes — and,
earlier, **ChronoRouter** (temporal-demand LLM routing). Reuse-first check found VariantGraph's five pieces
are ALREADY implemented in the backend (it IS the `MULTI-PATH-DEVELOPMENT` law, built):

| VariantGraph piece | Existing module (reuse, do not rebuild) |
|---|---|
| Variant registry | `src/teleon/compiler/registry.py` + `src/teleon/registry/port.py` + `standards/MULTI-PATH-DEVELOPMENT.md` |
| Constraint engine | `experiments/parallel_paths` contracts + `scripts/check_parallel_path_contracts.py` |
| Selector policy | `scripts/path_selection_policy.py` — `select_path(features)` → routing table `{class→ranked_paths+fallbacks}`, portfolio-never-lock-in, decisions to a policy ledger, auto-updates |
| Execution graph | `scripts/run_path_bakeoff.py` — races N paths on the SAME input via `parallel_paths.run_parallel` |
| Telemetry & learning | the policy ledger + receipts + `src/teleon/evolution/{descender,meta_learner}.py` (self-adapting) |

The only genuinely-new surface is the ergonomic `@variant` / `graph.run(capability, context)` DX — a thin
naming layer, not a framework.

## Decision
1. **Do NOT build/publish a standalone VariantGraph repo** (it would re-implement the above). The staging
   build was abandoned before any repo was created.
2. **VariantGraph = adopt the vocabulary over the existing engine.** If a developer-facing API is wanted,
   add a thin `@variant` / `graph.run` facade that DELEGATES to `path_selection_policy` + `parallel_paths`
   + the registry — never a parallel engine. (Facade vs document-only is an owner decision — asked; pending.)
3. **ChronoRouter** (`github.com/AIDoneRight/chronorouter`, private) stays as the public OSS FRONT for the
   temporal-routing thesis (the temporal-demand policy IS genuinely new), but its routing internals must
   **back onto the existing `foundry/model_route` + OIPS Inference Gateway**, not duplicate them. Portfolio
   home: **OpenRoutingHub** (the model-routing-policy registry). Its README already documents the mapping
   to the parallel-path/descent engine (honest reuse).

## Consequences
Zero duplicate engines. The multi-path thesis gets a name ("VariantGraph") + optionally an ergonomic head,
both over the one implementation. ChronoRouter is a marketable OSS funnel whose internals converge on OIPS.

## Enforcement / links
`standards/MULTI-PATH-DEVELOPMENT.md`; `scripts/{path_selection_policy,run_path_bakeoff}.py`;
`src/teleon/{compiler/registry,evolution/descender,registry/port}.py`; the reinvention guard
(`src/teleon/registry/reinvention_guard.py`) should list VariantGraph/ChronoRouter as known-existing.
