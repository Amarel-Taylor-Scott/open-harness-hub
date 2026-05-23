# Multi-model judging ensemble

*pipeline* · `pipeline/multi-model-judging-ensemble` · v0.1.0 · beta

Run inference across N different LLMs (e.g. Mixtral / Mistral-7B /
Gemma-7B / Llama-3-8B), score each model's prediction with a
perplexity baseline, then majority-vote or weighted-blend for final
output.

Verified by Open Harness Hub mining of aatiffraz's
"Prompt Prediction w/ Mixtral/Mistral7B/Gemma/Llama" (640 votes).

| axis | value |
|---|---|
| industry | ai |
| capability | reasoning, evaluation |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



## Task

Run N small-to-mid LLMs on the same prompt, score each with
perplexity baseline or judge, weighted-blend for final answer.

**pipeline_kind:** `ensemble`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `per_model_inference` | processor | `processor/action-sampler-multi-rollout` | — |
| 3 | `blend` | processor | `processor/multi-vector-fusion` | — |

