---
name: document-to-knowledge-graph
description: Extract a typed knowledge graph from a source document.
when_to_use: 'Pipeline kind: synthesis.'
---

# Document to knowledge graph (nodes + edges with source anchors)

Take any source document (contract, SOP, regulatory framework, supply-chain disclosure) and produce a typed knowledge graph with source-anchored nodes + edges. Implements the concept-graph-from-text pattern with three concrete node-type sets: contract-clauses, sop-steps, supply-chain-entities.

## Task

Extract a typed knowledge graph from a source document.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **page_chunk** — `processor` → `processor/page-aware-chunker`
4. **concept_graph** — `processor` → `processor/concept-graph-extractor`
5. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/local-first-research-tutor
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/citemind-architecture-reference`

## Success criteria

- deterministic `$.steps.concept_graph.output.unanchored_count` <= `5`

## Provenance

- Hub component: `pipeline/document-to-knowledge-graph` v0.1.0
- License: `MIT`
- Industry: legal, compliance, supply_chain, research
- Full source manifest: see `references/manifest.yaml`
