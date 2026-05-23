# Personal corpus search (RAG over user's own files / notes / docs)

*harness* · `harness/personal-corpus-search` · v0.1.0 · experimental

Search the user's personal corpus — their own files, notes,
emails, calendar, contacts — and return answer + citations
scoped to ONLY the user's data. Authorization-gated; refuses
to answer questions about a person from third-party data
unless the user has explicitly authorized.

Trust boundary is local — the user's data does not leave their
device unless they choose a hosted model arm.

| axis | value |
|---|---|
| industry | personal_productivity, cross_industry |
| capability | retrieval, reasoning, memory |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |

**Consumes:** `persona_block`, `rag_doc`, `tool_definition`

**Emits:** `reasoning_step`, `context_snippet`

**Contributes to:** `pipeline/personal-search-pipeline`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_claude` | `anthropic` | external | False | False |

## Logic paths

### query → personal corpus retrieve → cite-first answer  
*model_call: `required`*

1. load user preferences (incl. privacy gates)
1. scope retrieval to user's own corpus (calendar / contacts / notes / docs / emails)
1. retrieve top-K from each source (hybrid BM25 + dense)
1. rerank with cross-encoder
1. compose persona + retrieved + tool registry
1. generate answer with citations to source URIs / file paths
1. redact any third-party PII before answer is returned

**consumes:** `persona_block`, `rag_doc`, `tool_definition`

**emits:** `reasoning_step`, `context_snippet`

**verification:** every claim cites a personal corpus source URI, no third-party PII in answer body, no synthesis of information not actually in the corpus



## Privacy boundaries

- **raw_input**: the query stays on user's device
- **derived_output**: the answer stays with the user
- **external_calls**: only if model_target.trust_boundary == external AND user opted in via env

