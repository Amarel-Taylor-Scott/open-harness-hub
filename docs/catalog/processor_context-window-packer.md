# Context-window packer (Lost-in-the-middle aware)

*processor* · `processor/context-window-packer` · v0.1.0 · beta

Reorganize retrieved chunks into the model's context window so the
most important content lands at the BEGINNING and END of the window
(Liu et al. 2023 "Lost in the Middle"). Also enforces:
  - token budget cap
  - per-source dedup
  - chunk-priority ordering (rerank score → recency → source authority)
  - explicit chunk delimiters with index labels for citation
Returns the packed context string + chunk-index → source map.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | retrieval |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



