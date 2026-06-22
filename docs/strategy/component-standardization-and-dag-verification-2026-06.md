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

## Proposed next (seams 1 + 2 — design, needs greenlight; NOT built unilaterally)
- **Uniform `Component` wrapper** — one `invoke(typed_inputs) -> typed_outputs` adapter that normalizes any plane/port
  behind a single call shape, carrying its declared I/O types. Closes seam 1; makes "swap a component in/out" glue-free.
- **Spec → executable lowering** — `component_id -> Node` using that wrapper, so a compiled DAG actually RUNS on real
  ports (not just a synthetic dry-run). Closes seam 2.
- **Component conformance harness** — one generic test every adapter must pass to prove it satisfies its port's I/O
  contract (we have per-port drop-in tests; this makes conformance a single gate for any new component).

These are additive and reversible, but they touch execution semantics — recommend greenlight before building (change-
verification: design changes carry a warrant). The verifier above is the low-risk, high-value piece and is already in.
