# Per-document relevance grader (Self-RAG)

*processor* · `processor/document-grader` · v0.1.0 · experimental

Score each retrieved document for relevance to the user query. Emits
per-doc grade ∈ {relevant, irrelevant, ambiguous} with a confidence
score. Used by Self-RAG and CRAG to filter or trigger fallback.

Verified by Open Harness Hub clone: pattern shows up in Self-RAG's
reflection-token approach and is the canonical first step of
Corrective-RAG.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | verification, classification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



