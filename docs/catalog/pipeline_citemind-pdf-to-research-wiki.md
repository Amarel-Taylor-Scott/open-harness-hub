# Local PDF → research wiki + concept graph (CiteMind shape)

*pipeline* · `pipeline/citemind-pdf-to-research-wiki` · v0.1.0 · experimental

Local-first pipeline that turns a single PDF (paper / textbook chapter / report) into a persistent study workspace: OCR-aware indexing, hybrid retrieval, RAG chat with citations, generated wiki pages, study guides, and a concept graph — all on local storage with Ollama/Gemma. Port of the CiteMind hackathon submission (Tauri 2 + React 19 + Rust + SQLite).

| axis | value |
|---|---|
| industry | education, compliance, privacy |
| capability | retrieval, extraction, evaluation, format_conversion |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Turn a PDF into a persistent local research wiki with cited answers + concept graph.

**pipeline_kind:** `synthesis`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `pdf_extract` | processor | `processor/pdf-extract-with-ocr-fallback` | — |
| 2 | `page_aware_chunk` | processor | `processor/page-aware-chunker` | — |
| 3 | `embed_local` | processor | `processor/local-embedder` | — |
| 4 | `hybrid_retrieve` | processor | `processor/hybrid-bm25-vector-retrieve` | — |
| 5 | `cited_answer` | processor | `processor/llm-judge` | — |
| 6 | `wiki_generate` | processor | `processor/structured-to-prose` | — |
| 7 | `concept_graph` | processor | `processor/concept-graph-extractor` | — |
| 8 | `audit` | processor | `processor/audit-trace-emitter` | — |

