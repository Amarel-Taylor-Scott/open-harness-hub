# Curriculum Q&A dataset builder (PDF → PyMuPDF → chunks → LLM Q&A → clean)

*processor* · `processor/curriculum-qa-dataset-builder` · v0.1.0 · experimental

End-to-end processor that builds a domain-specific Q&A dataset from
curriculum PDF documents for on-device tutoring. Implements the
ShikshaEdge "build your own corpus" pattern:

  Stage 1 — PDF extraction: PyMuPDF extracts text page-by-page,
             preserving chapter/section headings as metadata.
  Stage 2 — Chunking: sliding-window sentence chunker (configurable
             window size, stride) with heading-aware boundary detection
             so chunks don't straddle topic boundaries.
  Stage 3 — Q&A generation: LLM generates question-answer pairs from
             each chunk (configurable max pairs per chunk). Output is a
             structured JSONL record: {chunk_id, question, answer, source_page}.
  Stage 4 — Clean + dedupe: heuristic filters remove trivially short
             answers (< 10 tokens), questions that are copies of headings,
             and near-duplicate Q pairs by Jaccard similarity.
  Stage 5 — Emit: writes a clean JSONL file ready for BM25/dense indexing
             and on-device RAG ingestion.

This processor is the corpus-acquisition primitive for any low-resource
domain where no existing Q&A dataset exists. It turns a PDF syllabus into
a retrievable knowledge corpus without requiring a cloud service.

CAPABILITY LIFT (structural): frontier models lack training data for
regional-language curriculum content (e.g., NCERT in Marathi, regional
State Board syllabi). A base model asked to tutor from these curricula
will hallucinate or fall back to English. This processor builds the
retrieval corpus that fills the sparse-data gap.
lift_reason: no_addressable_source (no public Q&A dataset for the target
curriculum) + sparse_data (model training signal for these domains is
thin); mechanism: context_length (the curriculum content cannot fit in
a bare model's implicit knowledge without fine-tuning or retrieval).

| axis | value |
|---|---|
| industry | education, education.k12, education.tutoring, cross_industry |
| capability | extraction, format_conversion, research |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | Apache-2.0 |



