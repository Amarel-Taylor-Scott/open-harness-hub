# Usage-gated compression (prediction-error retention)

*processor* · `processor/usage-gated-compress` · v0.1.0 · experimental

Prediction-error-gated context retention (the Friston move) — keep a usage prior learned from past turns and spend token fidelity only on surprising or load-bearing context (utility + volatility + recency), compressing the predictable, re-read-as-ritual remainder to FULL/SUMMARY/HANDLE_ONLY tiers under a budget. Cross-turn + model-external (unlike H2O's attention gate or LLMLingua's per-prompt perplexity) and it cuts PREFILL re-read cost. Lossless — paged-out items keep a rehydratable handle; a prediction miss re-promotes them.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | summarization |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



