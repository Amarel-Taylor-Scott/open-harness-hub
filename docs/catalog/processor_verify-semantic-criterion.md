# Semantic-similarity success-criterion evaluator

*processor* · `processor/verify-semantic-criterion` · v0.1.0 · beta

Evaluates one `kind: semantic` success criterion. Computes
embedding similarity between the target text and each reference
topic in `must_cover`; passes if EVERY topic clears
`similarity_threshold`. Implementation uses an embedder adapter
(default `adapter/bge-embeddings-local`).

Use this when regex is too brittle ("output mentions
HIPAA-equivalent context" — could be phrased many ways).

| axis | value |
|---|---|
| industry | cross_industry |
| capability | verification, evaluation, embedding |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



