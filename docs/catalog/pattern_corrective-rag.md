# Corrective RAG (CRAG)

*pattern* · `pattern/corrective-rag` · v0.1.0 · beta

RAG with a three-state retrieval evaluator. After initial retrieval,
an evaluator classifies the retrieval as {correct, incorrect,
ambiguous}. Correct → strip-and-recompose; incorrect → fall back to
web search; ambiguous → both. The evaluator's three-state output
prevents the "no relevant doc found" failure mode that breaks naive RAG.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | retrieval, verification |
| modality | text |
| lifecycle | beta |
| trust_boundary | external |
| license | CC-BY-4.0 |



