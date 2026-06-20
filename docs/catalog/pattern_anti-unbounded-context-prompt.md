# Anti-pattern: unbounded context prompt

*pattern* · `pattern/anti-unbounded-context-prompt` · v0.1.0 · stable

Feeding an LLM the entire available context — all retrieved chunks, all conversation history, all documents, all tool results — without a token budget, relevance gate, or compression step. The model's attention dilutes across irrelevant material and per-call cost grows unboundedly.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | generation, retrieval |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | CC-BY-4.0 |



