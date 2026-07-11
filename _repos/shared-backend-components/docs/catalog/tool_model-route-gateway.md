# Model route gateway

*tool* · `tool/model-route-gateway` · v0.1.0 · experimental

Provider-neutral model dispatch layer. Accepts a model registry
configuration listing local (Ollama, llama.cpp, vLLM), OpenAI-
compatible, managed (Anthropic, Gemini), and tenant-key endpoints.
Selects the target route based on requested capability, trust
boundary, latency hint, and available credentials, then forwards
the request using the matching transport. Returns a unified
response envelope regardless of provider.

| axis | value |
|---|---|
| industry | ai, cross_industry, software.devops |
| capability | routing, serving, tool_use |
| modality | text, multimodal |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



