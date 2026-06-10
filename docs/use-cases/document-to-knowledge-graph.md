# Use case: Document to knowledge graph (nodes + edges with source anchors)

Extract a typed, source-anchored knowledge graph from any structured document. Contract becomes clauses + cross-references. SOP becomes steps + dependencies. Regulatory framework becomes obligations + applies-to edges. Supply-chain disclosure becomes entities + sourcing edges.

Concrete pipeline: `pipeline/document-to-knowledge-graph`.

## Why graphs, not just text chunks

Chunks let you ask "what does the document say about X." Graphs let you ask the structural questions:

- which clauses cross-reference each other
- which SOP steps depend on which
- which obligations apply to which party
- which suppliers feed which sub-tier suppliers
- which methods produce which claimed results
- which regulatory section supersedes another

These questions cannot be answered by retrieval alone. A graph with typed edges + source anchors is the right representation.

## What the pipeline produces

```
nodes: [
  { id, type ∈ {clause, step, entity, person, obligation, right, deadline}, label, page, span },
  ...
]
edges: [
  { src, rel ∈ {depends_on, cross_references, supersedes, applies_to, defined_in, obligates, permits}, dst, page, span },
  ...
]
unanchored_count: integer  # nodes/edges without a (page, span) anchor
```

The pipeline succeeds when `unanchored_count <= 5`. Any larger value triggers human review of the un-anchored entries.

## Three concrete shapes

1. **Contract to clauses graph**: nodes are clauses + defined terms; edges are cross-references + supersedes + obligates. Pair with `persona/contract-reviewer`.
2. **SOP to step graph**: nodes are procedural steps; edges are depends_on + supersedes + applies_to. Pair with `persona/biosecurity-officer` or `persona/nuclear-safety-inspector` for regulated SOPs.
3. **Supply-chain disclosure to entity graph**: nodes are suppliers + sub-tier suppliers + commodities + jurisdictions; edges are sourcing + audit-finding + WRO-entity-match. Pair with `persona/esg-supply-chain-analyst`.

## Pattern + processor lineage

- Architectural pattern: `pattern/concept-graph-from-text` (extracted from the CiteMind submission).
- Storage shape: `pattern/source-document-to-persistent-knowledge-layer` (the graph is the durable representation, not the chat).
- Extractor: `processor/concept-graph-extractor` (typed nodes + edges with source anchors).
- Counter-pattern to avoid: `pattern/anti-un-cited-extraction` (every node + edge must carry an anchor).

## Visualization

The graph is exportable to GraphML, JSON-LD, or RDF. A small frontend can render selected subgraphs with citation hovers (CiteMind shape). For batch analytics, load nodes + edges into DuckDB or Neo4j.
