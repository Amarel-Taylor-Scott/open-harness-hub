---
name: multi-model-judging-ensemble
description: Run N small-to-mid LLMs on the same prompt, score each with perplexity
  baseline or judge, weighted-blend for final answer.
when_to_use: 'Pipeline kind: ensemble.'
---

# Multi-model judging ensemble

Run inference across N different LLMs (e.g. Mixtral / Mistral-7B /
Gemma-7B / Llama-3-8B), score each model's prediction with a
perplexity baseline, then majority-vote or weighted-blend for final
output.

Verified by Open Harness Hub mining of aatiffraz's
"Prompt Prediction w/ Mixtral/Mistral7B/Gemma/Llama" (640 votes).

## Task

Run N small-to-mid LLMs on the same prompt, score each with
perplexity baseline or judge, weighted-blend for final answer.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **per_model_inference** — `processor` → `processor/action-sampler-multi-rollout`
3. **blend** — `processor` → `processor/multi-vector-fusion`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default

## Provenance

- Hub artifact: `pipeline/multi-model-judging-ensemble` v0.1.0
- License: `MIT`
- Industry: ai
- Full source manifest: see `references/manifest.yaml`
