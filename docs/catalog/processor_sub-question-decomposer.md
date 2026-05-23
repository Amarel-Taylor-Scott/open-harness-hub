# Sub-question decomposer

*processor* · `processor/sub-question-decomposer` · v0.1.0 · beta

Break a compound question into N atomic sub-questions, each
independently answerable. Used by `pipeline/multi-doc-qa-subquestion`
and similar LlamaIndex SubQuestionQueryEngine flows.

Returns the sub-question list + a small dependency graph (e.g. Q3
depends on Q1's answer). The pipeline runtime can then schedule
retrieval / answering with the right ordering.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | reasoning |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



