---
name: citemind-pdf-to-research-wiki
description: Turn a PDF into a persistent local research wiki with cited answers +
  concept graph.
when_to_use: 'Pipeline kind: synthesis.'
---

# Local PDF → research wiki + concept graph (CiteMind shape)

Local-first pipeline that turns a single PDF (paper / textbook chapter / report) into a persistent study workspace: OCR-aware indexing, hybrid retrieval, RAG chat with citations, generated wiki pages, study guides, and a concept graph — all on local storage with Ollama/Gemma. Port of the CiteMind hackathon submission (Tauri 2 + React 19 + Rust + SQLite).

## Task

Turn a PDF into a persistent local research wiki with cited answers + concept graph.

## Steps

1. **pdf_extract** — `processor` → `processor/pdf-extract-with-ocr-fallback`
2. **page_aware_chunk** — `processor` → `processor/page-aware-chunker`
3. **embed_local** — `processor` → `processor/local-embedder`
4. **hybrid_retrieve** — `processor` → `processor/hybrid-bm25-vector-retrieve`
5. **cited_answer** — `processor` → `processor/llm-judge`
6. **wiki_generate** — `processor` → `processor/structured-to-prose`
7. **concept_graph** — `processor` → `processor/concept-graph-extractor`
8. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/local-first-research-tutor
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/citemind-architecture-reference`

## Success criteria

- rubric `rubric/citemind-citation-fidelity-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/citemind-pdf-to-research-wiki` v0.1.0
- License: `MIT`
- Industry: education, compliance, privacy
- Full source manifest: see `references/manifest.yaml`
