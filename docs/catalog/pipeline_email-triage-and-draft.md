# Email triage + reply draft

*pipeline* · `pipeline/email-triage-and-draft` · v0.1.0 · experimental

Customer-support email workflow. Layered chain:
  redact PII →
  grep (prompt-injection guard on email body — emails often carry attack
    content from untrusted senders) →
  classify intent (top-K from a controlled intent vocabulary) →
  route to the right specialist persona →
  retrieve account / policy context →
  draft response →
  human-review gate for sensitive intents (refund, legal, escalation).

Mirrors anthropic-cookbook `patterns/agents/routing`, langgraph
`examples/customer-support`, openai/swarm handoff.

| axis | value |
|---|---|
| industry | retail, retail.support, cross_industry |
| capability | classification, routing, reasoning, safety_gating |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given an inbound customer email, classify intent, retrieve relevant
account + policy context, draft a response, and route to a human if
the intent is sensitive (refund > $X, legal, escalation, threat).

**pipeline_kind:** `triage_email`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `redact_pii` | harness | `harness/redact-pii-text` | — |
| 2 | `guard_prompt_injection` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 3 | `classify_intent` | processor | `processor/intent-dispatcher` | — |
| 4 | `draft_response` | harness | `harness/text-safety-review` | — |
| 5 | `trace_audit` | processor | `processor/audit-trace-emitter` | — |
| 6 | `escalate_if_sensitive` | processor | `processor/escalate-human-review` | $.steps.classify_intent.output.selected_route IN ['human_review', 'legal_human_review'] |

