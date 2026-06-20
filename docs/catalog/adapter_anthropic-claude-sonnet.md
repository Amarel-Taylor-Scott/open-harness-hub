# Anthropic Claude Sonnet (frontier-class chat + tool-use)

*adapter* · `adapter/anthropic-claude-sonnet` · v0.1.0 · stable

Frontier-class generation + tool-use adapter using Anthropic's
Claude Sonnet (4.x family) via the official Anthropic API. Use as
the strongest generation arm in benchmarks, the "frontier judge"
in `judge: "frontier_judge"` benchmark configs, or as the model
in high-stakes ESG / clinical / legal pipelines where the trade-
off of API cost + external trust boundary is worth the quality.

Requires `ANTHROPIC_API_KEY` in env. Default model is the latest
Sonnet 4.x at instantiation time; override via `default_model`.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | generation, dialogue, tool_use, reasoning |
| modality | text |
| lifecycle | stable |
| trust_boundary | external |
| license | MIT |



