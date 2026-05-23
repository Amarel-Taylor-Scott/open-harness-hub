# Personal chat pipeline (preference + memory + tool-aware)

*pipeline* · `pipeline/personal-chat-pipeline` · v0.1.0 · experimental

Wraps `harness/chat-with-memory` in a concrete pipeline that
loads user preferences, resolves any tool calls, and persists
the turn to the memory backend.

| axis | value |
|---|---|
| industry | personal_productivity, cross_industry |
| capability | dialogue, memory, tool_use |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Multi-turn personal chat with preference + memory awareness.

**pipeline_kind:** `agent_loop`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_prefs` | processor | `processor/preference-loader` | — |
| 2 | `chat` | harness | `harness/chat-with-memory` | — |
| 3 | `leakage_check` | rule_pack | `rule-pack/grep-personal-info-leakage` | — |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | — |

