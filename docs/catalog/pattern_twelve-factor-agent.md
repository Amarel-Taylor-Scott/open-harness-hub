# Twelve-Factor Agent (principles for production-grade LLM software)

*pattern* · `pattern/twelve-factor-agent` · v0.1.0 · stable

A checklist-style design pattern for building LLM agents that are reliable
enough to put in front of real customers, adapted from HumanLayer's
"12-factor-agents". The thesis: most production "agents" are mostly
deterministic software with LLM steps inserted at carefully chosen points —
so own the prompt, the context, and the control flow rather than handing
everything to an autonomous loop.

The twelve factors:
 1. Natural language to tool calls — convert intent into structured calls.
 2. Own your prompts — treat prompts as first-class, versioned code.
 3. Own your context window — engineer what the model sees; do not let it
    grow unbounded (pairs with pattern/input-token-compression).
 4. Tools are structured outputs — a "tool call" is just the model emitting
    structured data your code acts on (pairs with
    pattern/strict-output-format-contract).
 5. Unify execution state and business state — one source of truth.
 6. Launch / pause / resume with simple APIs — agents are long-lived.
 7. Contact humans with tool calls — escalation is a first-class action.
 8. Own your control flow — branch, retry, and loop in your code, not in
    an opaque agent loop.
 9. Compact errors into the context window — summarize failures so the
    model can recover.
 10. Small, focused agents — many narrow agents beat one god-agent.
 11. Trigger from anywhere, meet users where they are — Slack, email, cron,
    API, not just a chat box.
 12. Make your agent a stateless reducer — (state, event) -> new state, so
    runs are replayable and testable.

In OpenHubForAI terms these map onto harnesses (own the prompt/model
boundary), tools (structured outputs), pipelines (own the control flow),
review tickets (contact humans), and replayable run records (stateless
reducer).

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | agent_loop, planning, tool_use, governance |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | mixed |
| license | CC-BY-4.0 |



