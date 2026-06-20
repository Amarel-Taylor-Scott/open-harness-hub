# Multi-vector / multi-query fusion (RRF + weighted)

*processor* · `processor/multi-vector-fusion` · v0.1.0 · stable

Fuse N ranked candidate lists from independent retrievers (sparse +
dense + graph + cross-encoder reranker output) via Reciprocal Rank
Fusion or weighted score blending. Returns a single deduped ranked
list.

Verified by Open Harness Hub clones: shape appears in
`Raudaschl/rag-fusion`, `superlinear-ai/raglite/_search.py`, and
`microsoft/graphrag/global_search/`.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | retrieval |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



