---
name: deepseek-r1-code-interpreter-math
description: Given a math word problem, generate a Python program that computes the
  answer, run it in a sandboxed kernel, parse the result. Repeat N times with diverse
  sampling; majority-vote the parsed answers.
when_to_use: 'Pipeline kind: tool_augmented_reasoning.'
---

# DeepSeek-R1 / QwQ + Python code-interpreter for math reasoning

The winning AIMO-2 shape: a reasoning-distilled LLM (DeepSeek-R1-
Distill-Qwen-7B / QwQ-32B) generates Python code that solves a math
problem, the code runs in a Jupyter / sandbox kernel, and the output
feeds back as the answer (or the LLM iterates if execution fails or
the answer is implausible). Majority-vote across N rollouts is the
standard ensembling.

Verified by Open Harness Hub mining: itahiro DeepSeek-R1-distill-7B
(1399 votes), lewtun "Updated Code Interpretation" (1173 votes,
Lewis Tunstall HF), mbmmurad QwQ-32B-preview optimized inference
(1097 votes), yekenot DeepSeek-R1-distill-7B-AWQ (1087 votes),
abdurrafae "Improved Code Interpretation" (1001 votes). 5-of-5 top
AIMO kernels follow this shape.

## Task

Given a math word problem, generate a Python program that computes
the answer, run it in a sandboxed kernel, parse the result. Repeat
N times with diverse sampling; majority-vote the parsed answers.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **rollouts** — `processor` → `processor/action-sampler-multi-rollout`
3. **execute_and_iterate** — `processor` → `processor/iterative-revise-loop`
4. **majority** — `processor` → `processor/multi-vector-fusion`
5. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/vllm-awq-local

## Provenance

- Hub artifact: `pipeline/deepseek-r1-code-interpreter-math` v0.1.0
- License: `MIT`
- Industry: ai, scientific_research, education
- Full source manifest: see `references/manifest.yaml`
