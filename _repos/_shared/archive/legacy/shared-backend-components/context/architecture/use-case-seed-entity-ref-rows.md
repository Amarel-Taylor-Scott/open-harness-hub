# Use Case Seed Entity Reference Rows

Use-case seeds need more than labels. Labels make filtering flexible, but a
million-object registry also needs graph-addressable entities so workers can
compare, block, cluster, and rerank objects by shared verticals, jurisdictions,
workflow stages, expected inputs, expected outputs, and risk concepts.

The seed row exporter now emits two additional row families:

- `canonical_entity`: stable graph nodes derived from domains, label paths,
  label ancestors, input types, output types, pipeline stages, and risk tiers.
- `object_entity_ref`: object-to-entity edges with roles such as `domain`,
  `risk_tier`, `label_path`, `label_ancestor`, `accepts`, `emits`, and
  `requires_stage`.

This keeps the hierarchy flexible without promoting every domain word into a
top-level taxonomy field. `capability` and `modality` remain broad routing
axes; detailed structure lives in labels, dimensions, and entity refs.

## Row Contract

Each seed-derived candidate primitive emits:

1. One `normalized_object` row.
2. One exact-hash `dedupe_cluster` row.
3. Many `label_assignment` rows for hierarchy and generated routing labels.
4. Many `dimension_value` rows for sortable/rankable features.
5. Many `canonical_entity` and `object_entity_ref` rows for graph traversal.
6. One review ticket when the seed has high, critical, or regulated risk.
7. Keyword, vector, graph, facet, and quality `index_record` rows.

Index records include linked entity IDs in metadata and graph edges, so search
workers can combine keyword, vector, facet, and graph evidence without
changing the source object shape.

## Comparison Use

Entity refs give comparison workers cheap blocking keys:

- same `domain` for broad candidate grouping;
- shared `label_ancestor` for hierarchy rollups;
- shared `requires_stage` for reusable pipeline-stage templates;
- shared `accepts` or `emits` for input/output compatible primitives;
- shared `risk_tier` for review and promotion batching.

The object-comparison job runner can use these keys before embedding
comparison, reducing n-by-m comparisons while still allowing fuzzy matching
inside each block.

## Scope Guard

Synthetic seeds in this batch continue to declare insurance as an excluded
scope. The exporter carries that exclusion in normalized object bodies,
labels, dimensions, and warnings, but does not mint insurance-specific
pipeline primitives.
