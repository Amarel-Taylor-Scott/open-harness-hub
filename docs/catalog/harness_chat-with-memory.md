# Persistent chat with memory (multi-turn, preference-aware)

*harness* · `harness/chat-with-memory` · v0.1.0 · experimental

Multi-turn chat harness with persistent memory across sessions.
Loads user preferences, recalls prior conversation context, and
honors the user's stated rules (don't reveal X, always cite Y,
decline Z requests).

Memory layers (Anthropic Memory tool / OpenAI threads /
LangGraph checkpointer / local file) are abstracted via
`memory_backend` config.

| axis | value |
|---|---|
| industry | personal_productivity, cross_industry |
| capability | dialogue, memory, tool_use |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |

**Consumes:** `persona_block`, `tool_definition`, `rag_doc`

**Emits:** `reasoning_step`, `context_snippet`

**Contributes to:** `pipeline/personal-chat-pipeline`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `anthropic_claude` | `anthropic` | external | False | True |
| `local_ollama` | `ollama` | local | False | False |

## Logic paths

### user turn → memory recall → preference check → response (tools as needed)  
*model_call: `required`*

1. load user preferences
1. recall conversation history (last N turns + summary of older turns)
1. for each user turn:
1.   detect intent (Q&A / action-request / vent / coaching / silent)
1.   if action-request: check tool_autonomy preference
1.   generate response respecting preferences
1.   optionally call tools (calendar / search / email-draft)
1.   redact PII from any externally-bound output
1.   persist turn to memory backend

**consumes:** `persona_block`, `tool_definition`, `rag_doc`

**emits:** `reasoning_step`, `context_snippet`

**verification:** no private-topic leakage when conversation forks to a different person, tool calls respect tool_autonomy preference, memory persistence respects retention preference



## Privacy boundaries

- **raw_input**: stays in the memory backend the user owns
- **derived_output**: stays with the user
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

