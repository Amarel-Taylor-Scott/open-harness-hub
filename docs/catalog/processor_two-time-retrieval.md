# Two-time retrieval (refine query, re-retrieve)

*processor* · `processor/two-time-retrieval` · v0.1.0 · beta

Retrieve top-K with the raw query, ask an LLM to compose a refined
query incorporating what was found, then re-retrieve. Final retrieval
set is the second pass (or union of both, deduplicated). Classic
Kaggle "EEDI two-time retrieval" shape — boosts recall on math-
misconception problems where the right answer needs concept-level
reformulation.

| axis | value |
|---|---|
| industry | ai, education |
| capability | retrieval, reasoning |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



