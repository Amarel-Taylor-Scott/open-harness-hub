# Quantized LLM inference (4-bit BitsAndBytes)

*pipeline* · `pipeline/quantized-llm-inference` · v0.1.0 · stable

Inference-only path: load a 7-70B LLM with 4-bit BitsAndBytes
quantization, run generation with controlled sampling kwargs and a
chat template. The lightest production shape — no LoRA, no fine-tune,
just memory-efficient inference for production deployments.

Verified across 5+ Kaggle kernels: cdeotte/starter-code-for-llama-8b,
itahiro/perplexity-baseline-phi-2-gemma-7b-it, richolson/{add-it-up,mash-it-up},
aatiffraz/prompt-prediction-w-mixtral-mistral7b-gemma-llama.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | generation, classification |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Load a 7-70B LLM with 4-bit quantization and run inference with a
defined chat template + generation kwargs.

**pipeline_kind:** `inference`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `infer` | harness | `harness/text-safety-review` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

