---
name: qwen-vllm-rerank-eedi
description: Given a math problem + a list of candidate misconception IDs (≈2.5k),
  retrieve the top-25 candidates via embedding, then constrain a Qwen- 32B-AWQ vLLM
  call (or 14B for cheaper) to output the single best ID.
when_to_use: 'Pipeline kind: retrieval_rerank.'
---

# Qwen-32B vLLM retrieval-rerank with logits-processor constraints

Two-stage retrieval pipeline that won EEDI Mining Misconceptions:
1. Embedding-based retrieve top-K candidate misconceptions
2. Constrain a Qwen-32B-AWQ vLLM call to emit ONLY one of the K
   candidate IDs (via logits-processor-zoo AllowedTokens) — the LLM
   reranks among a fixed candidate set, never hallucinates an unseen
   ID. Optionally two-time retrieval first to refine the query.

Verified by Open Harness Hub mining: jagatkiran Qwen14B-Retrieval-
Qwen32B-logits-processor-zoo (672 votes, EEDI), aerdem4 Eedi-Qwen32B-
vllm-with-logits-processor-zoo (594 votes, EEDI), takanashihumbert
Eedi-Qwen-2.5-32B-AWQ-two-time-retrieval (650 votes), anhvth226 EEDI-
11-21-14B (686 votes). Confirmed 4-of-4 across top EEDI kernels.

## Task

Given a math problem + a list of candidate misconception IDs (≈2.5k),
retrieve the top-25 candidates via embedding, then constrain a Qwen-
32B-AWQ vLLM call (or 14B for cheaper) to output the single best ID.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **two_time_retrieve** — `processor` → `processor/two-time-retrieval`
3. **rerank_with_constraint** — `processor` → `processor/vllm-batched-sampling`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/fact-checker
- **model_adapter**: adapter/vllm-awq-local
- **rule_packs**: `rule-pack/hybrid-retrieval-policy`

## Provenance

- Hub artifact: `pipeline/qwen-vllm-rerank-eedi` v0.1.0
- License: `MIT`
- Industry: ai, education
- Full source manifest: see `references/manifest.yaml`
