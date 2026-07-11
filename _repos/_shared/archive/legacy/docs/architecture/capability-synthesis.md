# Capability Synthesis — the Teleon capability compiler

**Status:** built + proof-gated (`check_capability_synthesis`, `check_synthesis_discipline`, `check_capability_ladders`).
`serves_truth=false` (the descent governs how cheaply/boundedly a capability runs; Baltor governs whether its output is true).

When a user writes a capability in plain language, Teleon **compiles** it: intent → outline → component DAG → verify →
alternatives, with every decision **branched, versioned, tested, and tracked**, and a disciplined process that keeps a
frontier LLM from jumping down a branch too fast. The LLM **proposes** within rails; the scaffold + tests + governance
**dispose**.

## The 5-stage flow (`architecture/capability_synthesis_pipeline.json`, `src/teleon/synthesis/intent_to_dag.py`)

| stage | what it does | draws on |
|---|---|---|
| 1. outline | classify the capability, pick its descent **ladder**, restate goal + constraints, list candidate approaches (don't pick yet) | `capability_planner`, `capability_ladders`, `tool_planes` |
| 2. fill | each step → ≥3 cheapest-first component **options** (deterministic before model) | `tool_registry`, `external_api_registry`, `module_bundles` |
| 3. dag + test | assemble the DAG; **test each node in isolation** before anything depends on it; then end-to-end | `synthesis_tree`, `ab_harness` |
| 4. verify | the **5W1H** ladder per node/group/DAG (who/what/where/when/why/how — provenance, freshness/CDC, why-this-rung, honest-failure) | `change_verification_contract` |
| 5. alternatives | challenge the path: ≥2 alternatives + pros/cons; *could a deterministic tool replace this model rung?* | `descent_method_catalog`, `optimization_heuristics` |

## Discipline — don't jump down too fast (`architecture/synthesis_prompt_templates.json`)

The prompts are **templated**, each carrying `must` / `avoid` / `track` rails and the standing discipline:
`enumerate_before_commit` · `deterministic_before_model` · `dont_jump_down_too_fast` · `test_before_descend` ·
`troubleshoot_before_backtrack` · `track_data_every_step` · `exhaust_before_unavailable` · `one_change_per_branch`.
`frontier_prompts(intent)` injects these + the live context into each stage.

**Troubleshooting ladder** (on a node failure, before abandoning a branch): reproduce → isolate → classify
(component-bug | wrong-component | missing-dep/key | data-issue | bar-too-high) → fix-in-place → try-alternative (new
branch) → backtrack → escalate-rung → honest-unavailable.

## Branch · version · backtrack (`src/teleon/synthesis/synthesis_tree.py`)

`SynthesisTree.synthesize(points, tester)` is DFS, cheapest-option-first. Each decision is a **branch**, versioned by its
decision-path (`A=a2/B=b2`). A node is `dead_end` (its own test failed), `abandoned` (it worked but no descendant solved —
we **jumped back up**), or `working`. **Every branch — winners and losers — is kept with lineage** (lossless law). If no
branch solves, it returns honest `None` (never a fabricated success).

## Escape — sprout / break out / try something new (`src/teleon/synthesis/strategist.py`)

Backtracking explores *within* a plan. When the whole plan dead-ends, `resilient_synthesize` runs an escalating ladder of
**escape strategies**, each producing a *new* plan with its own versioned tree + trace:

1. `sprout_same_plane` — add more same-plane components (new branches not in the original plan)
2. `add_external_apis` — try hosted external-API rungs (a different kind of component)
3. `add_bundles` — drop in a vetted module bundle (a macro sub-DAG)
4. `reframe_ladder` — decompose with a **different** capability ladder (a different shape entirely)
5. `llm_novel` — ask the frontier LLM for a brand-new plan (port; honest no-op offline)

First strategy that solves wins; all attempts kept (lossless); honest no-solution after every strategy is exhausted.

## Track data at every step (`src/teleon/synthesis/synthesis_trace.py`)

`SynthesisTrace.from_tree(tree)` produces one record per decision: version, choice, **alternatives considered**, test
outcome, **cost**, **confidence**, status. Aggregates: `total_cost`, `deterministic_ratio` (descent health),
`explored_vs_committed` (flags any node **jumped to without considering alternatives** — the "jumped down too fast"
detector). Persists as JSONL — this is the per-step telemetry the descent **brain** learns from (winners *and* losers).

## Grouped modules (`architecture/module_bundles.json`)

Vetted sub-DAG recipes the synthesizer drops in as macro-nodes: `doc_intake`, `web_research`, `entity_resolve`,
`retrieval_rag`, `stance_audit`, `field_parse`, `classify_route`, `plan_solve`.

## What still needs wiring (honest)

- Live **LLM port** filling each stage (today: deterministic registry scaffold; the prompts are produced for the port).
- Persisting the versioned tree + trace into `descent_attempt_store` so branches are **learned** across runs.
- Filling the remaining capability-ladder planes (coverage is computed + nudged by the adapters flywheel).
