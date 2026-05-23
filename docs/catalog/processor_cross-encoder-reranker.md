# Cross-encoder reranker

*processor* · `processor/cross-encoder-reranker` · v0.1.0 · beta

Re-rank a list of retrieved candidates with a cross-encoder model
(BAAI/bge-reranker-base, Cohere rerank-v3, or similar). Takes top-N
candidates from a hybrid retriever and returns the top-K most
relevant to the query. Typically used between hybrid retrieval and
context-window assembly.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | retrieval |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



