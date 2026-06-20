---
name: vllm-batch-llm-inference
description: Given N prompts and a vLLM-served model, batch-generate completions with
  shared KV cache + optional logits-processor-zoo constraints. Output structured completions
  for downstream scoring or ensembling.
when_to_use: 'Pipeline kind: serving.'
---

# vLLM batch LLM inference (with logits-processor-zoo)

Serve many prompts through a single vLLM engine with shared KV cache
+ prefix caching. Optional logits-processor-zoo entries
(SuppressTokens / AllowedTokens / FixedTokenBias) constrain output
to a fixed-format token grammar — useful for retrieval-rerank
letter outputs, JSON skeletons, or multiple-choice answers.

Verified by Open Harness Hub mining: jagatkiran Qwen14B-Retrieval-
Qwen32B-logits-processor-zoo (672 votes, EEDI), aerdem4 Eedi-Qwen32B-
vllm-with-logits-processor-zoo (594 votes, EEDI), itahiro DeepSeek-
R1-distill-7B (1399 votes, AIMO 2), mbmmurad QwQ-32B-preview (1097
votes, AIMO 2), yekenot DeepSeek-R1-distill-7B-awq (1087 votes).
Confirmed pattern in 7 of 35 mined kernels.

## Task

Given N prompts and a vLLM-served model, batch-generate completions
with shared KV cache + optional logits-processor-zoo constraints.
Output structured completions for downstream scoring or ensembling.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **serve** — `processor` → `processor/vllm-batched-sampling`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/vllm-awq-local

## Provenance

- Hub artifact: `pipeline/vllm-batch-llm-inference` v0.1.0
- License: `MIT`
- Industry: ai, education
- Full source manifest: see `references/manifest.yaml`
