---
name: chat-with-memory
description: Multi-turn chat harness with persistent memory across sessions. Loads
  user preferences, recalls prior conversation context, and honors the user's stated
  rules (don't reveal X, always cite Y, decline Z requests). Memory layers (Anthropic
  Memory tool / OpenAI threads / LangGraph checkpointer / local file) are abstracted
  via `memory_backend` config.
when_to_use: Use when the user needs dialogue. Use when the user needs memory. Use
  when the user needs tool_use. Particularly relevant for personal_productivity.
---

# Persistent chat with memory (multi-turn, preference-aware)

Multi-turn chat harness with persistent memory across sessions.
Loads user preferences, recalls prior conversation context, and
honors the user's stated rules (don't reveal X, always cite Y,
decline Z requests).

Memory layers (Anthropic Memory tool / OpenAI threads /
LangGraph checkpointer / local file) are abstracted via
`memory_backend` config.

## Applied layers

- `persona`
- `privacy`
- `tools`

## user turn → memory recall → preference check → response (tools as needed)

*model_call:* `required`

**Steps**

1. load user preferences
2. recall conversation history (last N turns + summary of older turns)
3. for each user turn:
4.   detect intent (Q&A / action-request / vent / coaching / silent)
5.   if action-request: check tool_autonomy preference
6.   generate response respecting preferences
7.   optionally call tools (calendar / search / email-draft)
8.   redact PII from any externally-bound output
9.   persist turn to memory backend

**Verification**

- no private-topic leakage when conversation forks to a different person
- tool calls respect tool_autonomy preference
- memory persistence respects retention preference

## Privacy boundaries

- **raw_input**: stays in the memory backend the user owns
- **derived_output**: stays with the user
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `anthropic_claude` | `anthropic` | external | False | True |
| `local_ollama` | `ollama` | local | False | False |

## Provenance

- Hub component: `harness/chat-with-memory` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
