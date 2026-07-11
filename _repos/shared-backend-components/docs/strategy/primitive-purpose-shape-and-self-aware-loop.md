# Primitives: purpose, shape, storage, search, use — and the self-aware generation loop

> Owner directive 2026-07-01 (memorialized). Understand what a primitive IS and how it is
> supported/shaped/searched/stored/used, so we generate GOOD, USABLE primitives; chart our savings
> (context · tokens · speed · memory) against the NUMBER of primitives + benchmarks; and detect when an
> area SATURATES (plateau) so we inject diverse random sprouting and move on to new industries / tasks /
> architectures. The system must be **continuously improving, self-aware, and intelligent** about its own
> primitive generation, result tracking, and template generation.

This is the canonical "what a primitive is and how the loop measures itself" reference. It reconciles the
edge-first program (`docs/goals/edge-first-composition-program.md`) with the REAL verified-card schema and
the running factory.

## 1. Ultimate purpose

A primitive is a **reusable capability CONTRACT** an AI agent retrieves *instead of reading code/docs*. The
thesis (measured, not asserted): an agent usually needs the smallest trustworthy contract that lets it
choose/call/wrap/test/modify a capability — not the implementation. At M0 this is a **486× context
reduction / 154k tokens saved** at black-box output equivalence (`scripts/primitive_lift_benchmark.py`).
We build for the **negative space** (where base models lack capability), admit on **lift AND durability**,
and every row stays `candidate=true / serves_truth=false` until a promotion gate passes.

## 2. Shape — the product-spec contract (the REAL schema)

A card is a PRODUCT SPEC: **input · output · transformation logic · features**, plus the trust/effect fields
that make hidden behavior safe. The verifier (`scripts/verify_primitive_candidates.py`,
`REQUIRED_FIELDS`) is the single source of the required shape:

- **Structural `kind`** — `"primitive"` | `"primitive_group"` ONLY (a group hides member edges behind one
  visible edge). This is coarse and verifier-enforced. The **family** taxonomy
  (`api.endpoint` · `algorithm.vector_search` · `tool.browser_automation` · `viz.chart` · `genai.*` …, 60
  kinds in `catalog/knowledge-packs/data/aidevexplorer-primitive-kind-families/`) goes in **`primitive_kind`**,
  NOT `kind`. (This mismatch rejected 690 cards on 2026-07-01 as `unsupported_kind` until fixed — recorded so
  it never recurs.)
- **Edges** — `input_edge` / `output_edge` (compact typed) + `*_description`; `dedupe_key` = normalized
  `input_edge->output_edge` (the identity for population dedupe).
- **`contract`** — `input` {type→desc}, `output` {type→desc}, **`transformation_logic`** (ordered steps — the
  product-spec "how"), `errors` (typed), `summary` (one sentence). *(transformation_logic + `features` were
  added 2026-07-01 per owner: product teams spec input/output/transformation logic.)*
- **`blackbox`** — one sentence: does-what, in→out, key side effect.
- **`edge_contract`** — composition notes (how a caller wires it); `group_contract` + `hidden_member_edges`
  for groups.
- **Trust/effect (safety-critical, first-class)** — `effects` (honest: network/db/file/model_call/
  cost/credential/…), `source_refs` (**public https URLs required** — the moat is governed provenance),
  `proof_requirements` (tests, always ending `candidate_boundary_gate`), `promotion_blockers`,
  `promotion_status`, `reuse_profile`, `features`.
- **Lineage** — `source_provider` / `source_model` / `source_shard_id` / `extracted_candidate_id`.
- **`candidate: true`, `serves_truth: false`** on every row.

**Templates** are slot-parameterized families above primitives (`base_kind`, `slots`, `slot_contracts`,
`example_instantiations`) — the population-control mechanism (pick the template, each typed slot collapses
shape-space). W10 template extraction was ~0 until the ultracode lane started emitting them.

## 3. Storage (W9 data plane — `architecture/primitive_data_plane.json`)

Shapes are policy, not accident:
- **Staging** stays long-format JSONL (`batch_runs/**/extracted/extracted_candidates.jsonl`) — the lossless
  raw layer.
- **Verified** → `verified_candidates/<run_date>/verified_candidates.jsonl` + manifest (verified / duplicate /
  rejected counts). The `<run_date>` prefix is how the daily total is globbed (`2026-07-01*`).
- **Operational tier** — normalized core (primitive/family/variation/route/template/slot/chain/receipt/
  affinity/negative-memory) in Postgres+pgvector, with DENORMALIZED wide search projections rebuilt from
  truth; **embeddings live LONG** (one row per embedding column per primitive — N columns, per-column
  method+dims, LSH bucket keys per column).

## 4. Search (edge-first, hybrid)

`src/teleon/registry/primitive_match.py` already has LSH blocking (profile + semantic bucket keys) + fit
classes (`exact` / `deterministic_edit` / `nondeterministic_edit` / `incompatible`) + adapter plans + chain
compatibility. Retrieval resolves by NAME/EDGE (grep-as-graph exact under the deterministic-naming law).
Ranking is multi-signal (receipts outrank embeddings; negative memory suppresses). **Nested disclosure**
(L1 edge card → L2 contract → L3 behavior → L4 route → L5 proof → L6 source slice → L7 full source): the
agent stays as shallow as the task allows — that shallowness IS the saving.

## 5. Use (composition)

Agents compose by reading **names + edges**, not bodies. A route = ordered primitives with adapters
(mutators) between; `compile_exact_edge_route` / `collapse_route_to_group_card` /
`plan_primitive_graph_runtime` in `src/teleon/primitives/groups.py`. Multiple doctrines coexist
(population + derivation + repair + path-policy); **receipts decide** which dominates per situation (the
all-paths tenet — W8).

## 6. The self-aware loop (measure → re-weight → sprout / move on)

```
generate  ->  verify (dedupe)  ->  TRACK (this loop)  ->  re-weight generation  ->  repeat
```

`scripts/track_primitive_saturation_and_savings.py` (proof-gated) is the instrument:
- **Charts** verified primitive count per **area (`primitive_kind`) × lane × industry** against measured
  **savings** (context 486× / tokens / memory / speed from the lift benchmark) — output:
  `data/dev-intel/primitive_saturation/<date>_saturation.{md,json}`.
- **Saturation signal (measured, cheap):** as an area fills shape-space, the fraction of newly-generated
  cards that are DUPLICATES rises. Per-area bands: `productive` (mine) · `watch` (diversify) · `saturated`
  (move on) · `cold` (too few to judge). Thresholds are named constants (single source).
- **Recommendations → next generation weights:** `keep_mining` rich veins · `sprout_diversity` (new
  domains/entities + random-sprout mutators) in watched areas · `move_on` from saturated areas ·
  `open_new_frontier` (new industry/architecture source families) when coverage is broad.

The intent: the factory READS its own saturation report and re-weights — scaling productive areas,
diversifying watched ones, abandoning plateaued ones, and opening new industries/tasks/architectures — so
generation is continuously improving and self-aware rather than blindly uniform.

## 7. Proving usefulness (benchmarks + the A/B simulation — in flight)

- **Deterministic proof:** `primitive_lift_benchmark` (edge-cards vs full-source, black-box equivalent) —
  the 486× headline.
- **Benchmark adapter catalog:** 240 external LLM/agentic benchmarks
  (`catalog/knowledge-packs/data/benchmark-lab-adapter-catalog/`) with A0–A8 comparison arms + L1–L7 depth.
- **Developer A/B simulation (next):** simulate developers across many companies × job titles doing real
  tasks under a **traditional LLM harness** vs a **primitive-search harness**, with adversarial red-teaming,
  measuring tokens/context/correctness/savings. This is the scaled, agent-driven version of the lift proof
  and the headline product claim.

## 8. Standing rules

Every generated row `candidate=true / serves_truth=false`; a report/benchmark is **evidence, never promotion
authority**. Distillation never replacement (losers sink to lineage). Adding a method is adding a PATH, never
replacing the incumbent. Deterministic vs probabilistic split is explicit (deterministic media/algorithms
validate by artifact metadata; genai wraps a probabilistic call in a deterministic envelope + safety +
provenance receipts).
