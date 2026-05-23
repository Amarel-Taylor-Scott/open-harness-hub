# Local vLLM engine with AWQ-quantized weights

*adapter* · `adapter/vllm-awq-local` · v0.1.0 · stable

Adapter for serving a local LLM via vLLM with AWQ (Activation-aware
Weight Quantization) weights. Used in the Kaggle "EEDI" and "AIMO 2"
competitions to fit Qwen-32B / DeepSeek-R1-distill-Qwen-7B / QwQ-32B
on a single T4 / L4 / A10 with high throughput. AWQ ≈ 4-bit but
preserves activation statistics → less perplexity drop than
bitsandbytes nf4.

Verified by Open Harness Hub mining: itahiro DeepSeek-R1-distill-7B
(1399 votes, AIMO 2), mbmmurad QwQ-32B-preview (1097 votes),
yekenot DeepSeek-R1-distill-7B-awq (1087 votes), aerdem4 EEDI Qwen32B
vLLM (594 votes), takanashihumbert EEDI Qwen-2.5-32B-AWQ (650 votes).
Confirmed pattern in 7 of 35 mined kernels.

| axis | value |
|---|---|
| industry | ai |
| capability | serving |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



