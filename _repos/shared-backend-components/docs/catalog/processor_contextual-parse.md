# Contextual AI Parse adapter (hosted document understanding → markdown + hierarchy)

*processor* · `processor/contextual-parse` · v0.1.0 · experimental

GOVERNED ADAPTER that WRAPS Contextual AI's hosted Parse engine
(`POST /parse`) as an OpenHubForAI processor component. This is a
thin wrapper over a third-party best-of-breed engine — OHH does NOT
rebuild it. Contextual's Parse converts PDF / DOC(X) / PPT(X) / PNG /
JPG (<300MB, <2000 pages) to clean Markdown or JSON, infers document
hierarchy, and attaches positional metadata to each chunk
(`parse_mode`, `enable_document_hierarchy`, `enable_split_tables`).
On OmniDocBench it scores 87.0 — a stronger document-understanding
engine than OHH's local OCR/extract stand-ins.

WRAP, NOT REPLACE — what OHH adds ON TOP of the external engine:
  - PROVENANCE: every parsed chunk is bound to its source_record with
    a content hash, so a downstream Knowledge Corpus carries where
    each fact came from — Contextual returns text + hierarchy, but the
    governed source binding is OHH's.
  - MEASURED-LIFT ADMISSION: this adapter is admitted into a pipeline
    only when paired measurement (`scripts/foundry/measure.py`) shows
    `pipeline_score - bare_model_score > 0` AND the lift is structural
    (`scripts/eval/reason_codes.py`); it is not admitted by vendor fiat.
  - COMPOSITION: it slots into the seven-primitive grammar as a pre-API
    Input/ingest step, interchangeable at the schema boundary with the
    local-first path below.

DETERMINISTIC / LOCAL FALLBACK: when no Contextual credentials are
configured (or for offline / no-cloud negative-space runs), the
pipeline falls back to the local-first ingest processor
`processor/doc-to-markdown-rag-ingest` (PyMuPDF / python-docx /
html2text). The hosted path is higher-accuracy; the local path is the
no-cloud default — complementary, not exclusive.

Hosted engine, external trust boundary, external_call side effect:
routed to the external-metered worker pool (see
context/backend/architecture/component-execution-and-runtime-routing.md). Requires
a Contextual AI API key. Cost (Contextual list pricing, 2026): $3 per
1k pages text, $40 per 1k pages multimodal — metered per call.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | extraction, format_conversion, retrieval |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | external |
| license | proprietary-saas-wrapped |



