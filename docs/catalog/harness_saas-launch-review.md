# SaaS launch landing-page review harness

*harness* · `harness/saas-launch-review` · v0.1.0 · experimental

Wraps the SaaS launch review flow as a reusable harness. Reviews
landing-page copy + tagline + pricing + demo materials against
corpus norms and anti-pattern rules; produces per-aspect findings
with severity, observation, corpus norm, and suggested rewrite.

| axis | value |
|---|---|
| industry | software, creative, cross_industry |
| capability | evaluation, extraction, reasoning |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**Emits:** `reasoning_step`, `context_snippet`, `extracted_fact`

**Contributes to:** `pipeline/saas-launch-critique`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Logic paths

### landing page → anti-pattern flags → corpus-norm RAG → per-aspect grade + rewrites  
*model_call: `required`*

1. extract tagline + ICP + feature list + pricing + demo info
1. fire SaaS-launch anti-pattern GREP pack
1. RAG against SaaS launch best-practices pack per aspect
1. judge per saas-launch-quality-v1 rubric
1. propose per-finding rewrites
1. emit audit trace

**consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**emits:** `reasoning_step`, `context_snippet`, `extracted_fact`

**verification:** every finding has aspect + severity + suggested rewrite, every rewrite is at most 1 sentence longer than the original, launch-day-blocker findings explicitly flagged



## Privacy boundaries

- **raw_input**: stays local; landing-page text is public
- **derived_output**: may sync to hub
- **external_calls**: only on explicit user opt-in

