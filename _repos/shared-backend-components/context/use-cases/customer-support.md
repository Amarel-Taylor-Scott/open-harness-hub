# Use case 4 - Customer-support email triage + draft

> Classify intent, retrieve account context, draft a reply, escalate sensitive issues.

## When to use

- Inbound support email triage
- Help-desk ticket routing
- Sales-inbox first-touch
- Forum-thread auto-reply (with human approval)

## Primary pipeline

[`pipeline/email-triage-and-draft`](../catalog/pipeline_email-triage-and-draft.md)

## Primitives used

| Layer | Component |
|---|---|
| Redact | `harness/redact-pii-text` |
| Guard | `rule-pack/grep-prompt-injection-heuristics` (emails often carry payloads from untrusted senders) |
| Classify | `processor/intent-dispatcher` with 8-intent vocabulary |
| Persona | `persona/support-agent` |
| Harness | `harness/text-safety-review` for the draft |
| Audit | `processor/audit-trace-emitter` |
| Escalate | `processor/escalate-human-review` (sensitive intents → ticket queue) |

## Composition

```
email_body
  → redact-pii-text
  → grep-prompt-injection-heuristics (emails from untrusted senders)
  → intent-dispatcher (billing | refund | product | complaint | legal | spam | feature_request | technical)
  → text-safety-review (persona/support-agent)  → draft reply
  → audit-trace-emitter
  → escalate-human-review IF intent in [refund, legal_threat]
  → intent_label, draft_reply, human_review_required, routing_decision
```

## Sample inputs / outputs

```python
inputs = {
    "email_body": "Your product overcharged me $200 last month. Refund or I'll dispute with my bank.",
    "sender_email": "<redacted>",
    "account_id": "ACCT-12345"
}
# → intent_label: "refund_request"
# → routing_decision: "human_review"
# → draft_reply:
#   "Thanks for writing in. I see you're asking about a charge from
#    last month. I've forwarded this to our billing team for a refund
#    review - they'll reply within one business day. Reference:
#    ACCT-12345."
# → human_review_required: true
```

## Install path

### Claude Code

```
/plugin marketplace add Amarel-Taylor-Scott/openhubforai@dist-published
/email-triage-and-draft
```

### Production deploy

Wire `pipeline/email-triage-and-draft` to a queue (SQS / GCS / Postgres LISTEN):

```python
from openhubforai import run_pipeline  # via scripts/run_pipeline.py
for email in queue:
    result = run_pipeline("pipeline/email-triage-and-draft", inputs={
        "email_body":  email.body,
        "sender_email": email.sender,
        "account_id":   email.account_id,
    })
    if result["human_review_required"]:
        ticket_queue.send(result)
    else:
        send_reply(email.sender, result["draft_reply"])
```

## Customization knobs

- **Domain-specific intents**: edit the `routes` list in step `classify_intent` (add `cancel_subscription`, `account_security`, `gdpr_request`, etc.).
- **Account-context retrieval**: add a `step` between intent and draft that pulls account data via `tool/<crm-lookup>` (write your own based on `tool/web-search`'s shape).
- **Different personas per intent**: chain `persona/support-agent` (default) → `persona/billing-specialist` for billing intents. Use a `processor/intent-dispatcher` step that selects the persona.
- **Compliance**: add `data_protection.purposes: [dpv:CustomerCare]` to the pipeline manifest. The `eu_ai_act_risk` field stays `minimal` for routine support (not "high-risk" under Annex III).
