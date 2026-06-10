# Chain-of-Density (iterative dense summarization)

*pattern* · `pattern/chain-of-density` · v0.1.0 · stable

Iteratively compress a summary by N rounds: each round the model
identifies a missing entity / fact from the source and rewrites the
summary to include it WHILE keeping length constant. After N
rounds the summary is denser (more facts per word) without
becoming longer. Useful for executive abstracts of long documents.

| axis | value |
|---|---|
| industry | ai, media, cross_industry |
| capability | summarization, reasoning |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | CC-BY-4.0 |



