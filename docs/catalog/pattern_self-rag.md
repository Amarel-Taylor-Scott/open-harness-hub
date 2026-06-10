# Self-RAG

*pattern* · `pattern/self-rag` · v0.1.0 · stable

Reflection-token retrieval-augmented generation. The model first
decides whether to retrieve at all, then grades each retrieved
document for relevance, generates an answer grounded in accepted
documents, then grades the answer for factual support. Iterates if
support is low. Distinct from naive RAG because every retrieval is
graded; distinct from CRAG because CRAG uses a three-state grader.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | retrieval, reasoning, verification |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | CC-BY-4.0 |



