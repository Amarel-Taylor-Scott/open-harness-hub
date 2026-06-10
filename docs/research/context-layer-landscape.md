# Context-layer landscape & Baltor's wedge (owner research 2026-06-05)

**Thesis:** Baltor should NOT be another memory product / vector DB / GraphRAG framework / generic
agent platform. Baltor's wedge is **governed context transformation**: decomposition, reconciliation,
freshness, lossless sidecars, deterministic promotion, receipts, safe consumption. Be the **context
governance & reconciliation layer that WRAPS** the other tools — not replace them.
(Reinforces [[governance-is-the-product]], [[moat-reframe-data-not-capability-gap]],
[[native-format-preservation]], [[lossless-distillation-law]], [[supermemory-competitor-complement]].)

## The market converges on four layers
1. **Memory / recall** — Supermemory, Mem0, Letta.
2. **Retrieval / GraphRAG** — LangChain, LlamaIndex, Haystack-style.
3. **Observability / evals** — Langfuse, Phoenix, LangSmith.
4. **Governance / reconciliation / provenance** — *Baltor's lane.* (Data-catalog cousins: OpenMetadata, DataHub.)
Most tools own 1–2 layers; production systems COMPOSE tools. Baltor governs whether context is valid,
reconciled, fresh, safe, consumable — and wraps the rest behind ports.

## Provider candidates (integrate behind ports; output = candidate, never truth; verify-first; never import as runtime)
| Slot | Candidates | Baltor role |
|---|---|---|
| `MemoryProviderPort` | supermemory (done), **mem0**, **letta** | recall → MemoryArtifact → verify/reconcile/consume |
| `TemporalGraphProviderPort` (NEW) | **Zep / Graphiti** (strongest match for fragile facts) | model changing facts; Baltor owns valid_at/authority/receipt/held-out/tenant/consumption |
| `ObservabilityProviderPort` (NEW) | **langfuse**, **phoenix**, **langsmith** | show what happened; Baltor proofs/flywheel stay the authority |
| `lineage` | **OpenLineage** | runtime lineage facets |
Graphiti is an open-source temporal context graph (valid_at/invalid_at, invalidates old facts as data
changes, vector+fulltext+graph in one retrieval) — exactly the fragile-fact / temporal-reconciliation shape.

## Standards to ADOPT in Baltor contracts (don't reinvent)
- **W3C PROV** — Entity (SourceArtifact/DerivedArtifact/ContextResponse) · Activity (Ingest/Decompose/
  Reconcile/Optimize Run) · Agent (Worker/Processor/LLMProvider/HumanReviewer). Map onto receipts/lineage.
- **OpenLineage facets** — extensible lineage; add a `LineageFacet` for Baltor fields (source authority,
  claim_status, verification/optimization receipts, held-out warnings).
- **W3C Web Annotation** — Body↔Target = the perfect model for sidecars (Target = original field/row/
  paragraph/PDF region/MD sentence; Body = verification note / conflict warning / receipt / reconciliation).
- **JSON Pointer + JSON Patch** — standard native_path + change ops for same-format JSON output.
- **XMP / C2PA** — validate that "native file + `.baltor.json` sidecar" is a mainstream enterprise pattern.

## Roadmap modules (research-driven; queued)
- **C-GRAPH-1 — Temporal Fact Graph** (Graphiti-inspired; powers fragile-fact watchtower + reconciliation):
  fields valid_at / invalid_at / observed_at / source_version / authority / tenant_scope / supersedes /
  contradicts / same_as_candidate / held_out_by / reconciled_by. **Highest-value next** — strongest fit
  with existing reconciliation + watchtower. Baltor owns which version is safe to serve.
- **C-RESEARCH-1 — Context Provider Catalog**: catalog memory.mem0@candidate, memory.letta@candidate,
  temporal_graph.graphiti@candidate, observability.{langfuse,phoenix,langsmith}@candidate,
  lineage.openlineage@candidate, annotation.web_annotation@v1, native.json_pointer@v1, native.json_patch@v1.
  Fits the existing external_capability_catalog + replacement-matrix machinery.
- **C-OBS-1 — Observability seam**: ObservabilityProviderPort + EvalProviderPort + SpanTree.v1 +
  ContextOperationSpan.v1; wrap Langfuse/Phoenix/LangSmith; Baltor proofs remain authority. (OTel/OpenInference adjacent.)
- **C-NATIVE-1 standards strengthening** (already shipped base): add formal JSON Patch + Web Annotation
  bodies + PDF/HTML/DOCX selectors to the sidecar (OPP-native-format).

## Positioning line (product promise)
"Bring your data in whatever format you already use. Baltor preserves the original shape, decomposes it
into governed context, reconciles contradictions, tracks freshness, optimizes context, and returns either
the same format with sidecars or a Baltor-native ContextResponse with receipts." Baltor = context
**governance & reconciliation authority**, not another memory API.

## Research queue to keep monitoring
Temporal graph memory (Graphiti/Zep, Hydra-style, WorldDB — content-addressed immutable nodes + recursive
containers + supersession/contradiction edges — validates lossless+reconciliation, don't adopt yet) ·
native+sidecar standards (Web Annotation, C2PA, OpenLineage facets, JSON Patch/Pointer, XMP) · memory
provider APIs (Supermemory/Mem0/Letta/Zep) · observability (Langfuse/Phoenix/LangSmith, OTel/OpenInference) ·
rule distillation (consensus→verified→deterministic, shadow→promotion — DONE as the Determinism Factory) ·
governed-context UX (memory graph UI, conflict workbench, sidecar viewer, source-handle browser, lineage
viewer, held-out panel — partially DONE via the 6 live surfaces).
