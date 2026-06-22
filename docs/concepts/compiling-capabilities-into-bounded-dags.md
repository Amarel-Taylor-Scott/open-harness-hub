# Compiling a capability statement into the most efficient, bounded, verified DAG — from millions of components

How Teleon turns a natural-language **capability statement** (or a conversation) into a **running pipeline**: it retrieves
the right components out of a registry **designed to scale to millions**, has an LLM **compose** them into a DAG, then
**bounds, verifies, and descends** that DAG to the cheapest path that provably works — and runs it on real ports.

The one-line version: **the LLM proposes; the registry, the type system, and the descent dispose.** The model never
writes the pipeline freehand and it never sees millions of components — it picks from a small, retrieved, *typed* set of
**real** components, and every choice is checked before anything runs.

---

## Why the obvious approaches don't work at this scale

- **"Put the catalog in the prompt."** You can't fit millions of components in a context window, and even thousands
  blow the budget and bury the model. → We **retrieve** a small candidate set first (RAG, but over components).
- **"Let the LLM write the code/workflow freehand."** Unbounded, unverifiable, and it hallucinates tools that don't
  exist. → The model may only pick from **real retrieved components**; an invented one is **rejected, never run**.
- **"Just wire the nodes (n8n/Zapier-style)."** That builds *a* workflow; it doesn't make it *cheap* or *correct*. →
  We **compile** to the cheapest **bounded** path and **verify** it before execution.

---

## The pipeline (end to end)

```
   capability statement  /  conversation
            │  natural-language intent
            ▼
┌────────────────────────────────────────────────────────────────────┐
│ 1. RETRIEVE   millions of components  →  a small candidate pool       │
│    layered registries (curated core · staged-massive · vector index) │
│    hybrid search: lexical + vector + Reciprocal Rank Fusion (RRF)    │
│    + capability-ladder rungs  + access-policy filter (per user/plan) │
└────────────────────────────────────────────────────────────────────┘
            │  ~dozens of REAL, TYPED, PERMITTED components
            ▼
┌────────────────────────────────────────────────────────────────────┐
│ 2. COMPOSE    the LLM orchestrates a DAG from the pool                │
│    sees each component's typed I/O  (consumes → produces)            │
│    rule: DETERMINISTIC-first; use the LLM only for the residual      │
│    guardrail: a hallucinated component is REJECTED                   │
│    validate → ONE repair retry with the errors fed back              │
└────────────────────────────────────────────────────────────────────┘
            │  nodes + edges  (a candidate DAG)
            ▼
┌────────────────────────────────────────────────────────────────────┐
│ 3. BOUND & VERIFY    is it a *verified working* DAG?                  │
│    acyclic · every edge type-compatible (GATING) · every input       │
│    satisfied by an upstream producer or a graph input · terminal     │
│    output · a dry-run through the real executor                      │
└────────────────────────────────────────────────────────────────────┘
            │  verified_working DAG
            ▼
┌────────────────────────────────────────────────────────────────────┐
│ 4. DESCEND    make it the *most efficient* bounded path              │
│    cheapest VIABLE component per choice-point that meets the bar     │
│    deterministic rungs  →  cheap LLM  →  frontier  (LLM is last)     │
└────────────────────────────────────────────────────────────────────┘
            │  the bounded, cheapest-viable DAG
            ▼
┌────────────────────────────────────────────────────────────────────┐
│ 5. EXECUTE & GOVERN    run on real ports; govern the output          │
│    uniform Component.invoke; lower → run on real ports               │
│    serves_truth=false on compute; Baltor verifies truth-bearing out  │
│    honest-unavailable — never a fabricated result                    │
└────────────────────────────────────────────────────────────────────┘
```

### 1. Retrieve — millions of components → a small candidate pool
The catalog is **layered** so it can grow without drowning the model:

- **Curated core** — vetted components the descent reads directly (config tier: JSON in git).
- **Staged-massive** — scraped/harvested candidates (thousands → millions) kept **candidate-only** in JSONL → loaded to
  **Postgres + pgvector** (operational tier). They are **not** read by the descent until they cross the **promotion
  boundary** (source + dedupe + content-hash + license + review).
- **Search index** — every component is **labeled** with text, keywords, and a **vector**, so it's findable by meaning,
  not just exact name.

For one capability statement we run **hybrid search** — lexical **and** vector retrieval fused with **Reciprocal Rank
Fusion** (a doc strong on either signal ranks well, with no score calibration) — and add the rungs of any matching
**capability ladder**. The result is a **candidate pool of a few dozen real components**, already filtered by the
**access policy** (a given user/plan only sees components they're permitted to use). *This is the step that makes
"millions" tractable: the model sees dozens, never millions.*

### 2. Compose — the LLM orchestrates a DAG from real components
The LLM is the **orchestrator**, not a freehand author. Its prompt lists the candidate pool **with each component's
typed I/O** (`io = consumes → produces`) and the discipline: **deterministic components first; use the LLM step only for
the residual a deterministic component cannot do.** It returns a DAG as `{nodes, edges}`.

Three guardrails turn that proposal into something trustworthy:
- **No hallucination** — any node whose component isn't in the pool is **dropped** (the registry is the source of truth).
- **Type-aware composition** — because the model sees `consumes → produces`, it connects type-compatible edges; any
  remaining mismatch is surfaced.
- **Validate + one repair retry** — on malformed JSON / a cycle / a rejected component, the errors are fed back once and
  the model retries (the universal best practice from structured-generation systems).

### 3. Bound & verify — *is this a working DAG?*
A spec being acyclic and hallucination-free isn't enough. `verify_buildable_dag` promotes verification to a real verdict
— `verified_working` requires **all** of:
1. **acyclic** (a pipeline, not a loop);
2. **every edge type-compatible** — the upstream produces a type the downstream consumes (**gating**, not a warning);
3. **every input satisfied** — each node's consumed types come from an upstream producer or a declared graph input (no
   dangling input);
4. a **terminal output** node;
5. a **dry-run** through the *real* executor on synthetic typed data (proving the abstract spec lowers to a runnable graph).

This is where "**bounded**" is enforced: each component is a **bounded, typed, governed unit**, and the whole graph is
proven to fit together before a single real call is made.

### 4. Descend — the *most efficient* bounded path
Efficiency is **compilation, not luck**. A capability is a cost-ordered, **deterministic-first** ladder of choice-points;
the DAG executor resolves each choice-point by picking the **cheapest viable** component whose measured quality clears the
requirement floor — text before OCR before vision; regex/parser before classical-ML before cheap-LLM before frontier;
cheap search before premium grounded search. The model is the **last** rung, used only for the residual nothing cheaper
can cover. This is the "**make it work, then make it efficient**" descent — the same idea a compiler/query-planner uses.

### 5. Execute & govern
A **uniform Component wrapper** gives every component one shape — `invoke(typed_inputs) → typed_outputs` — over otherwise
bespoke ports (an LLM, an embedder, a reranker, an OCR engine all look the same to the DAG). The verified spec is
**lowered** to the real executable graph and **run on real ports**. Governance is non-negotiable:
- compute outputs carry `serves_truth=false` — they're **candidates**, not asserted truth;
- a **truth-bearing** answer is dispositioned by **Baltor's verification rail** (provenance, verify gate, CDC);
- if a component's lane/provider is offline it returns **honest-unavailable** — **never a fabricated result**.

---

## Conversation & refinement
A capability rarely lands perfectly on the first pass, so composition is a **decision tree with backtracking**: the
synthesizer tries the cheapest path, and on a dead end **jumps back up** and tries the next alternative — keeping the
losing branches (lossless) so a later turn can revisit them. When no direct composition exists, **escape strategies**
kick in (sprout a missing sub-capability, reframe the goal, pull a bundled recipe, or — last — propose a novel
component). In a conversation, each user clarification re-runs retrieval + composition against the refined intent; the
**verified_working** verdict and the per-component **dry-run** are what let the system say "this will work" or "this
edge doesn't type-check" *before* spending money or making outward calls.

---

## Why this is stronger than the alternatives
| | n8n / Zapier | raw "LLM writes it" | **Teleon** |
|---|---|---|---|
| component grounding | node catalog | none (invents) | **retrieved real components; hallucinations rejected** |
| DAG / branching | partial (Zapier linear) | unstructured | **real DAG, acyclic, branch/loop/choice** |
| cost / determinism | — (just wires) | most expensive by default | **deterministic-first descent to the cheapest viable path** |
| verified before run | manual | no | **type-checked + satisfiable + dry-run = verified_working** |
| swap a component | per-node config | n/a | **uniform invoke + conformance gate (proof-gated swap)** |
| truth | not addressed | hopes | **serves_truth=false + Baltor verification rail + honest-unavailable** |

---

## Module map (grounded — this is real, not a sketch)
- **Retrieve**: `src/teleon/synthesis/component_search.py` (label + search + compose), `src/teleon/retrieval/hybrid.py`
  (Reciprocal Rank Fusion over the vector + lexical ports), `architecture/capability_ladders.json`,
  `architecture/registry_layers.json` + `data/dev-intel/tool_registry_staging.jsonl` (the staged-massive tier),
  `src/teleon/storage/record_store.py` (config / operational[SQLite·Postgres+pgvector] / history tiers),
  `src/teleon/runtime/access_policy.py` (who may use what).
- **Compose**: `scripts/compile_capability_live.py` (`candidate_pool`, `intelligent_compile`, validate + repair retry,
  type-aware grounding), `src/teleon/synthesis/intent_to_dag.py`, `src/teleon/synthesis/synthesis_tree.py` (backtracking)
  + `strategist.py` (escape strategies).
- **Type contracts**: `architecture/plane_io_contracts.json` + `src/teleon/synthesis/io_contracts.py` (`edge_compatible`).
- **Bound & verify**: `src/teleon/synthesis/dag_contract.py` (`verify_buildable_dag` → `verified_working`).
- **Descend**: `src/teleon/dag/pipeline_dag.py` (`DAG.choose` cheapest-viable per choice-point),
  `architecture/optimization_passes.json`.
- **Execute**: `src/teleon/components/` (`Component.invoke`, `lower_to_dag`, `run_compiled`, `assert_conforms`),
  `scripts/compile_capability_live.py:compile_and_run` (one call: intent → compiled → verified → executed).
- **Govern**: `serves_truth` flags throughout; Baltor's verification rail; the promotion boundary; honest-unavailable.

## Invariants (always true)
- The LLM never sees millions of components — it sees a **retrieved, typed, permitted** candidate pool.
- A component the registry doesn't know is **never** in a built DAG.
- "Efficient" means **deterministic-first, cheapest-viable** — the LLM is the last rung, not the default.
- "Bounded" means **typed + satisfiable + dry-run-verified** before execution, and **honest-unavailable** at runtime.
- Compute output is a **candidate** (`serves_truth=false`); truth is dispositioned by Baltor, with provenance.
