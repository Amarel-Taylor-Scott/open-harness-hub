# Registry-based pipeline orchestration — typed I/O, standardized objects/refs, logging/lineage

Research (2026-06-22) on how RAG / search / hybrid / agent systems build DAGs from component registries and manage the
DATA FLOW (typed I/O, standardized inter-component objects, references-not-blobs, logging/lineage). To confirm + guide our
shared-I/O spine + the compiler. discovery≠trust.

## How the incumbents structure component I/O + data flow
- **Haystack 2.x** — explicit **TYPED pipelines**: every component declares typed inputs/outputs, connections are
  explicit, the **type system catches mismatches BEFORE runtime**; the pipeline is a DAG serializable to **YAML** (config,
  git-committable, loadable at runtime); **each component logs its inputs + outputs**. (The gold standard for typed,
  inspectable, registry-style pipelines.)
- **LlamaIndex Workflows** — **event-driven**: an `@step` consumes a typed **Event** and returns a new one; a **Context**
  API holds shared state; nested workflows share state. (Inter-step object = a typed event.)
- **LangGraph** — graph **state channels**: nodes are steps, edges are transitions, typed state flows through the graph.
- **OpenLineage** (the lineage/logging STANDARD) — models a run as **Job / Run / Dataset** entities + extensible
  **facets** (atomic metadata); **events are JSON** emitted over HTTP/Kafka; **Datasets are REFERENCES** (table/bucket/
  topic identifiers), i.e. you log/pass the pointer + schema, not the blob.
- **RAG orchestration** — a **DAG of components** (branches + loops) + a standardized **function-calling** tool interface;
  **hybrid retrieval** = vector + BM25 combined via **Reciprocal Rank Fusion (RRF)**; **RAGOps** (arXiv 2506.03401) for
  operating these pipelines (observability per stage).

## Map to OUR architecture — what we already have (confirm) + what to adopt
| concern | incumbent pattern | us |
|---|---|---|
| typed component I/O | Haystack typed ports, pre-runtime type-check | Shared I/O + Resource Spine (schemas/, ResourceRef/SecretRef) — but planes had no declared I/O TYPE → **ADOPT: plane I/O contracts + type-aware edge validation** *(this pass)* |
| standardized object between steps | Haystack typed objects / LlamaIndex events | the typed I/O spine; **pass a ResourceRef (pointer), not a blob** — CONFIRMED primitive ([[shared-io-resource-spine]]); ensure the compiled DAG threads refs |
| logging / lineage | OpenLineage Job/Run/Dataset + facets, JSON events | OpenLineage ADOPTED (standards interop manifest) + the record_store streams + per-step `synthesis_trace` + receipts — **confirm receipts map to OpenLineage facets** |
| references not blobs | OpenLineage Datasets = identifiers | ResourceRef/SecretRef = typed pointers + content-hash ids (the staged/version streams) — CONFIRMED |
| DAG as config | Haystack YAML, git | `capability_ladders.json` + the composed DAG (serializable JSON) — CONFIRMED |
| hybrid retrieval | vector + BM25 + RRF | retrieval ladder has BM25 (rank_bm25) + vector (faiss) + rerank — **ADOPT: Reciprocal Rank Fusion as the combine** |

## Our differentiators (none of these frameworks do these)
- **Deterministic-first COMPILATION** (the descent) — they wire/execute a DAG; we compile it to the cheapest bounded path.
- **Governance** — provenance + verify gate + serves_truth + honest-MISSING (Baltor); OpenLineage logs lineage, it doesn't
  govern truth.
- **No-hallucination registry guardrail** + **backtracking/escape** in composition.

## Concrete ADOPT
1. **Plane I/O contracts + type-aware edge validation** — each tool-plane declares the object TYPE it consumes/produces
   (e.g. ocr: bytes→text; reranker: (query,docs)→ranked_docs; embedding: text→vector); the compiler validates that an
   edge connects compatible types (Haystack's pre-runtime check / Langflow's port filter). *(implemented this pass:
   architecture/plane_io_contracts.json + check_plane_io_contracts.)*
2. **ResourceRef threading** — the composed DAG passes typed refs (pointers) between nodes, not blobs (confirm + wire).
3. **OpenLineage-shaped run events** — emit each component run as a Job/Run/Dataset event + facets (our receipts/trace → OL).
4. **Reciprocal Rank Fusion** — add RRF as the hybrid-retrieval combine microstep.
