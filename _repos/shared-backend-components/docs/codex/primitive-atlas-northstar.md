# Primitive Atlas North Star

Last updated: 2026-07-02

Status: north-star mission doc for the Primitive Atlas — the primitive-registry
layer of the portfolio. Every numeric target in this trio is a **goalpost, not a
measured fact**. Nothing here is a savings, benchmark, or customer-impact claim.
Current repo state is never typed into this doc: recompute it from the owning
manifest.json files and checkers named below.

Companion docs in this trio:

- [`primitive-atlas-million-primitive-roadmap.md`](primitive-atlas-million-primitive-roadmap.md) — the scale roadmap and its reconciliation with existing scale plans.
- [`primitive-atlas-telemetry-and-savings-model.md`](primitive-atlas-telemetry-and-savings-model.md) — the measured-savings math and the formulas-with-placeholders.

## Position in the existing north stars (supersedes nothing)

The Primitive Atlas mission is the **primitive-registry layer** of the product
north stars that already govern this repo. It adds a layer; it replaces nothing:

- [`docs/strategy/north-stars.md`](../strategy/north-stars.md) stays canonical for
  strategy: negative-space corpus acquisition, the two-axis lift-and-durability
  admission gate (`scripts/eval/reason_codes.py` is the single source of the
  taxonomy), screen-before-collect, governance/provenance as the external moat,
  maintenance over acquisition, and maximum interop. The Primitive Atlas is how
  those principles apply to **reusable executable capability** (primitives,
  primitive groups, templates, routes) rather than to fact corpora.
- [`docs/codex/north-star.md`](north-star.md) stays canonical for the product
  sequence (verification toolkit → sanctions beachhead → Baltor productization →
  measured-lift harness → open funnel). The Primitive Atlas is the registry
  substrate those milestones draw reusable capability from.
- [`docs/codex/master-goal.md`](master-goal.md) stays canonical as the master
  goal; [`docs/codex/million-object-goal.md`](million-object-goal.md) stays
  canonical for the registry-wide million-component objective. The roadmap doc in
  this trio reconciles with both instead of duplicating them.
- The portfolio law holds unchanged: Baltor → Teleon → OpenHubForAI, never the
  reverse (`architecture/portfolio_dependency_law.json`). In that frame, Teleon
  compiles intent into proofed deterministic routes over the Atlas, AIDevObserver
  detects repeated AI-development waste and recommends Atlas routes, and
  OpenHubForAI is the open registry substrate the Atlas lives on.

If this doc ever disagrees with those, they win; update this doc in the same
change.

## The category

The Primitive Atlas is not only a component library, a snippet pile, code
search, RAG over code, or a workflow-automation catalog. The internal category
is a **proof-aware primitive route market**: a massive searchable primitive
database so AI development systems stop wasting time, tokens, money, and risk
repeatedly recreating capabilities that already exist.

Core sentence:

> Search first. Reuse first. Remix deterministically. Generate only the missing
> edge. Prove every route. Promote only after receipts. Remember failures as
> negative memory.

## The core loop

```text
user intent
-> compact edge search
-> CandidateBundle (exact + near matches, templates, mutators, wrappers,
   source refs, proof obligations, negative-memory warnings, ranking explanation)
-> deterministic remix, or bounded generation ONLY for the missing edge
-> PlanLock (canonical, hashable, replayable, versioned compiled route)
-> deterministic execution or bounded controlled runtime
-> ExecutionReceipt (input/output hashes, route + primitive ids, effects,
   proof results, latency, cost, tokens)
-> telemetry
-> promotion, demotion, negative memory, or gap queue
-> registry memory
```

A model working over the Atlas should usually see only the smallest useful
contract: visible input edge + visible output edge + black-box behavior +
effects + proof status + source/evidence status + ranking explanation +
negative-memory warnings. It escalates to source depth only when the route
requires it.

## The invariant

**Compact context at the model boundary, proofed deterministic capability at
the runtime boundary.**

Everything in the Atlas serves this invariant: edge cards shrink what the model
must read; deterministic factories, proof gates, and receipts guarantee what
actually runs. The north-star metric family is therefore *hidden work per
visible edge* and *context avoided per task* — never raw row counts (see the
telemetry doc in this trio).

## Lifecycle (candidate until promoted)

Every primitive, group, template, route, and derived record moves through a
staged lifecycle:

```text
L0  discovered candidate
L1  source-backed candidate
L2  contract extracted
L3  effects declared
L4  proof obligations generated
L5  route compiled
L6  PlanLock emitted
L7  deterministic execution tested
L8  receipt recorded
L9  benchmark score recorded
L10 promoted, deprecated, retired, or negative-memory only
```

Default state at every stage before L10 promotion:

```json
{
  "candidate": true,
  "serves_truth": false
}
```

No model, no LoRA adapter, no mini-agent, and no benchmark row can promote
truth by itself. Promotion requires deterministic proof receipts plus the
review gates the promotion boundary already defines (see CLAUDE.md "Promotion
Boundary" and `docs/codex/lossless-distillation.md` — distillation is never
replacement; losers keep lineage).

## The eight never-forget rules

```text
1. Metrics decide.
2. Proof decides.
3. Receipts decide.
4. Candidate remains candidate until promoted.
5. Search first.
6. Reuse first.
7. Remix deterministically.
8. Generate only the missing edge.
```

Rules 1–3 mean no path, method, model, or ranker wins by sounding better; it
wins on comparable receipts. Rule 4 is the truth boundary above. Rules 5–8 are
the cost-ordered ladder for every request: exact reuse beats template fill
beats deterministic remix beats bounded generation beats source-level fallback.

## Non-commitment principle (portfolios of paths)

Do not commit the system to one way of generating primitives, one way of
searching for them, one way of compiling routes, or one way of proving them.
Maintain portfolios — generation paths, search paths, route-planning paths,
compilation paths, runtime-lowering paths, proof paths, repair paths,
promotion paths, negative-memory paths — where every path produces comparable
receipts, and data, metrics, policy, and logic decide which path wins for a
given task family. The route compiler's standing question:

> Which path solves this task with the least source escalation, least runtime
> model use, strongest proof, lowest side-effect risk, and best reuse value?

Full path catalogs and the problem-solution primitive core live in
[`claude-fable-compiled-primitive-routes-handoff.md`](claude-fable-compiled-primitive-routes-handoff.md),
which remains the operational handoff this north star distills.

## Where current state lives (never typed here)

- Verified candidate totals: computed by summing
  `data/dev-intel/primitive_factory/verified_candidates/*/manifest.json`
  via `scripts/report_multilane_primitive_generation.py`.
- Saturation and plateau state per area:
  `scripts/track_primitive_saturation_and_savings.py`.
- Measured context/token/memory savings: `scripts/primitive_lift_benchmark.py`
  and its summary output under `data/dev-intel/primitive_lift_benchmark/`.
- Daily lane capacity plans and their gates:
  `scripts/check_primitive_throughput_lanes.py` and
  `scripts/check_primitive_factory_5k_lanes.py`.
- Docs-contract freshness for this trio:
  `scripts/check_primitive_atlas_northstar_docs.py`.
