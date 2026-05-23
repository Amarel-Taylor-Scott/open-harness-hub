---
name: quantized-llm-inference
description: Load a 7-70B LLM with 4-bit quantization and run inference with a defined
  chat template + generation kwargs.
when_to_use: 'Pipeline kind: inference.'
---

# Quantized LLM inference (4-bit BitsAndBytes)

Inference-only path: load a 7-70B LLM with 4-bit BitsAndBytes
quantization, run generation with controlled sampling kwargs and a
chat template. The lightest production shape — no LoRA, no fine-tune,
just memory-efficient inference for production deployments.

Verified across 5+ Kaggle kernels: cdeotte/starter-code-for-llama-8b,
itahiro/perplexity-baseline-phi-2-gemma-7b-it, richolson/{add-it-up,mash-it-up},
aatiffraz/prompt-prediction-w-mixtral-mistral7b-gemma-llama.

## Task

Load a 7-70B LLM with 4-bit quantization and run inference with a
defined chat template + generation kwargs.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **infer** — `harness` → `harness/text-safety-review`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default

## Provenance

- Hub artifact: `pipeline/quantized-llm-inference` v0.1.0
- License: `MIT`
- Industry: ai, cross_industry
- Full source manifest: see `references/manifest.yaml`
