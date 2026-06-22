# Component standardization layers + verified-working DAGs (2026-06-22)

Answer to "do we need more standardization layers / thin wrappers / compatibility verification for building verified
working DAGs with many components?" — grounded in the code, so we add the connective tissue, not redundant frameworks.

## What we already have (do NOT re-invent)
- **Agnostic ports** — `select_X("auto")` + `register_X_adapter` drop-in for llm / browser / ocr / embedding / reranker /
  search / record_store / execution-provider. The swap layer: a future provider drops in with zero caller change.
- **Typed I/O contracts** per plane (`architecture/plane_io_contracts.json`) + `io_contracts.edge_compatible`.
- **Executable DAG** (`src/teleon/dag/pipeline_dag.py`) — `Node(fn, consumes, produces)` on a shared bus; If/Loop/choice/
  merge; cheapest-viable descent; a receipt; raises on missing-producer/cycle.
- **Shared I/O spine** (ResourceRef/SecretRef — typed pointers, not blobs) + `record_store` storage port.

## The three real seams (the thin wrappers worth adding)
1. **Bespoke ports aren't unified.** `complete(system,user)` vs `embed(text)` vs `rank(query,docs)` vs `search(query)` —
   no single `invoke(typed_inputs) -> typed_outputs` shape, so composing arbitrary components needs per-plane glue.
2. **The compiled spec is never lowered to the executable DAG.** `compile_capability_live` emits abstract `{nodes,edges}`;
   `pipeline_dag` runs hand-written pipelines. Nothing resolves a component ID to a runnable, typed `Node`.
3. **Verification is structural, not type-level or execution-proven.** We had acyclic + hallucination + type *warnings*
   (non-gating). A *verified working* DAG needs gating type-compatibility + satisfiable inputs + a real dry-run.

## Built this pass — seam 3 closed (and seam 2 partially bridged)
`src/teleon/synthesis/dag_contract.py` `verify_buildable_dag(nodes, edges)` → a `verified_working` verdict requiring:
acyclic · every EDGE type-compatible (gating) · every node's consumed types satisfied by an upstream producer or a graph
input (no dangling input) · a terminal OUTPUT node · a **dry-run through the real `pipeline_dag` executor** on synthetic
typed data (proving the abstract spec lowers to a runnable graph). Un-typed planes never false-fail. Wired into the
compiler as a stricter tier above `accepted`; proof `scripts/check_dag_contract.py`. serves_truth=false.

## Built (seams 1 + 2 + conformance — greenlit "build all, maximum flexibility") — `src/teleon/components/`
- **Uniform `Component` wrapper (seam 1)** — `registry.py`: one `Component.invoke(typed_inputs) -> typed_outputs` over
  every bespoke port. A `_PLANE_INVOKERS` registry maps each plane to an invoker wrapping its real port (llm/embedding/
  reranker/search/ocr wired; others HONESTLY unavailable — never a fabricated output). `register_component_invoker(plane,
  fn)` is the drop-in hook (a future port = zero caller change). `make_component(id)` types it from plane_io_contracts.
- **Spec → executable lowering (seam 2)** — `lowering.py`: `lower_to_dag(nodes, edges)` turns the abstract compiled spec
  into a real `pipeline_dag.DAG` whose nodes gather typed inputs (by type) from predecessors + graph inputs and call the
  uniform invoke; `run_compiled(...)` RUNS it end-to-end on real ports through the executor (proven offline: ocr-stub ->
  real lexical embedding).
- **Conformance harness** — `conformance.py`: `assert_conforms(component)` is the single gate — invoked with synthetic
  inputs for its consumed types, an adapter must return a dict with >=1 declared produced type OR raise
  ComponentUnavailable honestly; a wrong-type output FAILS. Swap-in is now proof-gated.

Proof: `scripts/check_component_standardization.py`. The compiler's `composed_dag` (step/component/plane per node) is
exactly `lower_to_dag`'s input, so a `verified_working` compiled capability is directly runnable via `run_compiled`.
serves_truth=false throughout (a run yields candidates the verification rail dispositions).
