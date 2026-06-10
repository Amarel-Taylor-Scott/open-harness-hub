# Gemma-4 primitive graph tagger

*processor* · `processor/gemma-primitive-graph-tagger` · v0.1.0 · experimental

Use Gemma 4 (text-only is fine — multimodal optional) to tag every
catalog primitive (harness, pattern, processor, rule-pack, persona,
rubric, knowledge-pack, adapter, dataset, pipeline) with typed
graph edges that make the catalog more searchable.

Reads a primitive's manifest (name, description, tags, industry,
capability) and emits:
  - typed nodes: { id, kind, label, source_anchor }
  - typed edges: {
      src_id: <primitive id>,
      rel: <edge type>,
      dst_id: <other primitive id OR vocabulary term>,
      confidence: 0..1,
      rationale: "<one-line>"
    }

Edge types (kept small on purpose):
  - related_to           — neighbor primitive (same task domain)
  - composes_with        — frequently used in the same pipeline
  - alternative_to       — substitute for the same step
  - extends              — generalization-of relationship
  - emits_signal         — output that another primitive consumes
  - consumes_signal      — input that another primitive emits
  - mitigates            — anti-pattern / risk this primitive guards against
  - depends_on_taxonomy  — vocabulary term (industry / capability / modality)

The output edges are written back into the `edges` table of
`dist/catalog.sqlite` (the same table the hybrid-mode scaffold
search reads), so:
  1. Token-poor queries surface the right primitives via semantic
     neighbors that Gemma 4 declared related.
  2. The scaffold's edge-aware boost reflects "Gemma thinks these
     ship together," not just "they share a pipeline manifest."

| axis | value |
|---|---|
| industry | compliance, media, ai |
| capability | extraction, classification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



