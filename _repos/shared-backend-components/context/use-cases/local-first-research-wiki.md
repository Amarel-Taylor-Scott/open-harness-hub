# Use case - Local-first research wiki for PDFs (CiteMind shape)

## What

Turn a single PDF (paper, textbook chapter, technical report, regulatory framework) into a **persistent local study workspace**:

- read the original PDF with page-anchored navigation
- ask questions and get answers with page-span citations
- generate wiki pages, study guides, and a live concept graph
- keep notes and bookmarks attached to specific passages
- run entirely on the user's machine via Ollama / local embeddings

This use case bundles the **CiteMind** hackathon submission (Gemma 4 Good) into the catalog as a first-class vertical + extracts three reusable patterns that travel to other verticals.

## Who it serves

- **Students + self-learners** working through difficult material without unlimited cloud access
- **Researchers** triaging papers offline (flights, low-connectivity environments)
- **Regulated workflows** (legal review, medical record study, defense documentation) where documents cannot leave a controlled perimeter
- **Compliance auditors** building a persistent layer over a regulatory framework (e.g. 40 CFR Part 261 + 262 + 263) instead of re-reading from scratch each session

## How it maps into the catalog

- **Pipeline**: `pipeline/citemind-pdf-to-research-wiki` - 7-step chain: PDF extract w/ OCR fallback → page-aware chunk → local embed → hybrid retrieve → cited answer → wiki + concept graph → audit trace.
- **Persona**: `persona/local-first-research-tutor` - answers only from the document; every claim carries (page, span); refuses to fabricate.
- **Knowledge pack**: `knowledge-pack/citemind-architecture-reference` - the architectural shape itself, indexable + queryable.
- **Rubric**: `rubric/citemind-citation-fidelity-v1` - 7 dims, with `local_only_traffic` + `persistence_across_sessions` + `refusal_on_missing` as load-bearing.
- **Processors**: `processor/pdf-extract-with-ocr-fallback`, `processor/page-aware-chunker`, `processor/local-embedder`, `processor/hybrid-bm25-vector-retrieve`, `processor/concept-graph-extractor`.
- **Dataset placeholder**: `dataset/citemind-pdf-samples`.

## Three patterns extracted

1. **`pattern/local-first-with-cited-answers`** - generalizes to legal review, defense documentation study, BSL-4 SOP study, refugee Inkasso letter review.
2. **`pattern/source-document-to-persistent-knowledge-layer`** - generalizes to compliance audit notes, regulatory framework cross-references, ESG disclosure review.
3. **`pattern/concept-graph-from-text`** - generalizes to ESG materiality maps, supply-chain knowledge graphs, drug-interaction graphs, DFARS clause flow-down maps.

## Why this matters for the catalog

CiteMind is the second hackathon submission integrated as a first-class catalog vertical (after [Bill_info AI](./refugee-bureaucracy-translation.md)). Both submissions share a structural lesson the catalog now encodes explicitly:

> The right boundary for "local AI" is usually not "no cloud ever" - it is "the document stays local; every output cites a span; the user can verify."

The catalog promotes that boundary from a one-shot UX choice to a reusable pattern with attribution back to the upstream submission.

## Attribution

The CiteMind port is licensed MIT; catalog port credits "OpenHubForAI contributors" as port author and the CiteMind team as primary upstream. Direct upstream repo URL + author handle pending CiteMind team confirmation.
