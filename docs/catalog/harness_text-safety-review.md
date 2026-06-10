# Text Safety Review

*harness* · `harness/text-safety-review` · v0.1.0 · beta

A general-purpose text harness that composes persona + GREP +
RAG + tools + (optional) online grounding around a model call.
Designed to produce cited, bounded, citation-first responses.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | safety_gating, retrieval, reasoning, dialogue |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `grep_rule`, `rag_doc`, `citation_edge`, `tool_definition`, `persona_block`, `context_snippet`

**Emits:** `reasoning_step`, `context_snippet`

**Contributes to:** `pipeline/research-entity`, `pipeline/verify-claim-against-corpus`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `openai_compatible` | `openai_compatible` | external | False | False |
| `anthropic_judge` | `anthropic` | external | False | False |

## Logic paths

### Prompt → grounded cited response  
*model_call: `required`*

1. normalize chat messages
1. redact PII (via rule-pack/privacy-pii-text-en)
1. fire GREP rules; record severity hits
1. retrieve top-k RAG with BM25, optional dense, RRF merge
1. expand retrieved docs with 1-hop citation graph
1. compose persona + retrieved context + tool registry
1. call model
1. stream response + per-layer trace
1. verify every claim cited

**consumes:** `grep_rule`, `rag_doc`, `citation_edge`, `tool_definition`, `persona_block`

**emits:** `reasoning_step`, `context_snippet`

**verification:** layer trace recorded, citation coverage check, rubric score >= 0.6



## Privacy boundaries

- **raw_input**: stays local to the running harness process
- **derived_output**: may be synced to the hub only after anonymization gate
- **external_calls**: only when model_target.trust_boundary == 'external' AND user opted in

