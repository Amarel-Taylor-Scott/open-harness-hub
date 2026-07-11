# Teleon = the compiler for cognitive work (a self-improving workflow OS) — 2026-06-22

Two external framings (shared by the owner) crystallize what Teleon already is: not an agent framework, but a
**compiler/optimizer for autonomous work** — *"first make it work, then make it efficient automatically."* The
invariant: **every workflow begins maximally flexible and progressively converges toward bounded, deterministic,
efficient execution** (the descent). This doc maps both framings onto our REAL modules with honest coverage, so we
build only the genuine gaps. serves_truth=false.

## The 8-layer architecture → what we already have
| Layer | What it is | Our module(s) | Status |
|---|---|---|---|
| 1 · Intent Compiler | plain English → workflow DAG (IR) | `src/teleon/capability_planner.py` (text→typed plan) + `src/teleon/dag/` + `architecture/pipeline_step_catalog.json` | **partial** — routes to a capability + has a DAG; not yet full multi-node decomposition from English into a `{node,input,output,confidence,cost,execution_mode}` IR |
| 2 · Brute-force universal executor | solve by any means (correctness first) | the **unbounded** mode in `architecture/agentic_loop_catalog.json` + the cascade `frontier_only` baseline | **have** (modeled) |
| 3 · Execution trace + telemetry | token/latency/retry/confidence **per step** | `descent_attempt_store` records before/after **descents** | **gap** — per-*step* telemetry DB not built |
| 4 · Optimization discovery | find inefficiencies → candidates | the **descent** + `architecture/descent_method_catalog.json` (17 axes×methods) + `architecture/optimization_passes.json` (10 passes) + `scripts/eval/reason_codes.py` | **have** (taxonomy) / **partial** (auto-discovery on a trace) |
| 5 · Supervisory intelligence | architect/cost/reliability/safety review of changes | multi-model panel (`scripts/panel_review.py`, Kimi+GLM+Claude) + the descent brain + `stall_breaker` | **partial** — have multi-model review + the brain; not the named roles editing a DAG |
| 6 · Transformation engine | rewrite the DAG (e.g. node exec_mode GPT→small) | `src/teleon/evolution/catalog_descent.py` + the registry converter | **partial** — converts catalog entries; not live-DAG node rewrites |
| 7 · Validation sandbox | run the new version vs benchmark; accept only if not-worse | `src/teleon/evolution/ab_harness.py` + the lift gate + determinism **shadow mode** + the lossless run-side-by-side law | **have** |
| 8 · Version history | every change stored, diffable, rollback (GitHub-for-workflows) | `descent_attempt_store` (versioned, lossless, rollback target) + the Git backend port | **have** (versioned attempts; DAG-diffs are the gap) |
| User constraint layer | yaml: max_cost / min_accuracy / max_latency / allowed tools | **PreferenceProfile** (user multi-objective weights+constraints) + `OrgGuardrailPolicy` | **have** |
| Guardrail layer | never delete auth/compliance; never below the accuracy floor | `OrgGuardrailPolicy` + the verify gate + the change-verification contract + boundary approvals | **have** |
| Optimization knowledge base | learned patterns ("PDF→OCR first") | `descent_attempt_store` IS the meta-learner memory (`best_strategy_for`) + the method catalog | **have** |

## The 10 optimization passes (compiler passes)
Single-sourced in `architecture/optimization_passes.json`, each bound to a real descent axis + the module that runs it
(`check_optimization_passes`): context-minimization, retrieval-compression, deterministic-replacement, model-downgrading,
state-compression, parallelization, tool-specialization, caching, boundary-detection, reasoning-distillation. **6 have,
4 partial.** The 7 registries the passes draw replacement candidates from all exist: tool_planes, OpenContextHub
(context packs), the Knowledge Corpus / If-Statement (knowledge), the method catalog (deterministic logic), the model
index (models), the descent_attempt_store (execution-trace/learned KB).

## The moat (per the framing) — and our coverage
The moat is **the optimization feedback loop + workflow rewriting + execution telemetry + learned optimization KB** —
not the agent. We already hold three of four: the **learned KB** (the descent brain), the **optimization passes**
(the descent + method catalog), and the **validation/loop** (ab_harness + the flywheel). The missing quarter is the
**live execution telemetry + DAG rewriting** — exactly the genuine gaps below.

## Genuine gaps (queued as proposals — the remaining moat-work)
1. **Per-step execution telemetry** (Layer 3): a trace DB capturing tokens/latency/retry/confidence per DAG node — *you
   can't optimize what you don't measure.* The most foundational gap.
2. **Intent→DAG compiler** (Layer 1): plain English → a multi-node workflow IR (the `{node,input,output,confidence,
   cost_estimate,execution_mode}` graph) — extends `capability_planner` from single-capability routing to a DAG.
3. **Transformation engine on the live DAG** (Layer 6): rewrite a node's `execution_mode` / insert a preprocessing node
   from the trace, producing a new workflow version.
4. **Closed workflow-rewrite loop**: assemble execute→trace→diagnose→transform→sandbox→deploy→repeat over a live
   workflow (the pieces exist — descent, ab_harness, brain, guardrails; the assembly on a workflow DAG is the gap).

## Positioning
Not "an AI agent." Teleon is **the compiler for cognitive work** / a **self-improving workflow OS**: it does for
agentic cognition what LLVM passes / Spark query planning / TensorFlow graph optimization did for compute. Baltor
governs what each step treats as *true*; Teleon governs how cheaply + boundedly the whole workflow *runs*.
