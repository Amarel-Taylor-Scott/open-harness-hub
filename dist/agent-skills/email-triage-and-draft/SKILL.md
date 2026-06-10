---
name: email-triage-and-draft
description: Given an inbound customer email, classify intent, retrieve relevant account
  + policy context, draft a response, and route to a human if the intent is sensitive
  (refund > $X, legal, escalation, threat).
when_to_use: 'Pipeline kind: triage_email.'
---

# Email triage + reply draft

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

## Task

Given an inbound customer email, classify intent, retrieve relevant
account + policy context, draft a response, and route to a human if
the intent is sensitive (refund > $X, legal, escalation, threat).

## Steps

1. **redact_pii** — `harness` → `harness/redact-pii-text`
2. **guard_prompt_injection** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
3. **classify_intent** — `processor` → `processor/intent-dispatcher`
4. **draft_response** — `harness` → `harness/text-safety-review`
5. **trace_audit** — `processor` → `processor/audit-trace-emitter`
6. **escalate_if_sensitive** — `processor` → `processor/escalate-human-review` (when `$.steps.classify_intent.output.selected_route IN ['human_review', 'legal_human_review']`)

## Defaults

- **persona**: persona/support-agent
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/privacy-pii-text-en`, `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- rubric `rubric/research-entity-v1` threshold 0.7

## Provenance

- Hub artifact: `pipeline/email-triage-and-draft` v0.1.0
- License: `MIT`
- Industry: retail, retail.support, cross_industry
- Full source manifest: see `references/manifest.yaml`
