# vLLM batched sampling (SamplingParams + logits processors)

*processor* · `processor/vllm-batched-sampling` · v0.1.0 · stable

Issue an LLM batch through vLLM's `LLM.generate` (or
`llm.chat`) with `SamplingParams`. Optional `logits_processors`
(e.g. logits-processor-zoo: SuppressTokens, FixedTokenBias,
AllowedTokens) constrain output structure server-side.

Concrete pattern from EEDI Qwen-14B/32B kernels and AIMO-2
DeepSeek-R1-distill kernels — same shape, swappable model.

| axis | value |
|---|---|
| industry | ai |
| capability | serving, generation |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



