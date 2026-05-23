# AWQ-quantized LLM inference (alternative to bitsandbytes nf4)

*pipeline* · `pipeline/awq-quantized-inference` · v0.1.0 · stable

Serve a 4-bit AWQ (Activation-aware Weight Quantization) checkpoint
for inference. AWQ preserves activation statistics, generally
delivering lower perplexity drop than naive nf4. The de-facto
Kaggle pattern when you need 32B+ in 24GB of VRAM AND care about
quality (vs bitsandbytes when you care about LoRA training).

Verified by Open Harness Hub mining across 7 of 35 kernels:
takanashihumbert EEDI-Qwen-2.5-32B-AWQ (650), yekenot AIMO-2-DeepSeek-
R1-distill-7B-awq (1087), mbmmurad QwQ-32B-AWQ (1097), aerdem4 EEDI-
Qwen32B-vLLM (594), jagatkiran Qwen14B + Qwen32B-AWQ (672), itahiro
DeepSeek-R1-distill-7B (1399, vLLM serves AWQ).

| axis | value |
|---|---|
| industry | ai |
| capability | serving, generation |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Load an AWQ-quantized checkpoint via vLLM (or transformers + AutoAWQ),
run inference with batched prompts, return completions + per-token
logprobs. Drop-in alternative to bitsandbytes nf4.

**pipeline_kind:** `serving`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `infer` | processor | `processor/vllm-batched-sampling` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

