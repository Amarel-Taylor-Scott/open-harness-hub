# Doc-to-markdown RAG ingest (any document → markdown + auto-summary → scoped per-task RAG)

*processor* · `processor/doc-to-markdown-rag-ingest` · v0.1.0 · experimental

End-to-end document ingestion processor for the Trove local agentic
framework. Converts any supported document format (PDF, DOCX, HTML,
plain text, Markdown) to clean Markdown, generates a one-paragraph
auto-summary using a local LLM call, and writes both the Markdown body
and the summary into a per-task scoped RAG store (BM25 + optional dense
index). Each task in Trove gets its own isolated RAG scope so documents
loaded for one gem do not pollute the context of another.

Pipeline stages:
  1. Format detection — sniff MIME type and route to the appropriate
     converter (PyMuPDF for PDF, python-docx for DOCX, html2text for HTML,
     passthrough for plain text/Markdown).
  2. Markdown conversion — emit clean Markdown preserving heading hierarchy.
  3. Auto-summary — one LLM call with a fixed "summarise this document in
     one paragraph" prompt; result stored alongside the Markdown body.
  4. Chunk + embed — sliding-window chunker (configurable) → BM25 index
     update; optional dense embedding if a local embedding model is
     configured.
  5. Scope registration — write an index record associating the document
     with the gem/task ID so retrieval queries are automatically scoped.

CAPABILITY LIFT (structural): bare model context windows cannot hold entire
documents (especially multi-page PDFs), so a model asked to answer questions
from a document must hallucinate or fail. This processor builds the
retrieval layer that makes on-device RAG from arbitrary documents possible
without a cloud service. The gap is structural (context-length physical
limit). lift_reason: no_addressable_source (no cloud service; all local);
mechanism: context_length (document exceeds context window).

| axis | value |
|---|---|
| industry | ai, cross_industry, education, legal |
| capability | extraction, research, retrieval, format_conversion |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



