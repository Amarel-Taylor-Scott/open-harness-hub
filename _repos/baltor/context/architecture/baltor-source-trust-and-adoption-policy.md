# Baltor Source Trust And Fact Adoption Policy

Baltor should not adopt a new fact just because one source or one model says it.
New facts must pass source, evidence, trust, and injection checks before they can
be served to agents.

## Adoption Rule

Default rule:

- A new external fact needs at least two independent supporting sources before
  promotion.
- One source can be enough only when it is the authoritative source of record
  for that fact, such as an official regulator, government register, court,
  company filing, or customer-designated internal authority.
- If sources disagree, keep the fact out of served context until precedence,
  effective date, and scope are resolved.

Each adopted fact should record:

- current fact
- original customer fact when applicable
- supporting sources
- source roles
- retrieved timestamps
- source hashes
- archive capture status
- trust score
- adoption decision
- refresh policy

## Fact State Lineage

Facts should keep a state history, not only a final status. This lets Baltor
revisit promising but under-supported facts later.

Recommended states:

- `candidate_detected`: extracted from customer context or external source.
- `one_source_found`: one relevant source supports the candidate.
- `two_sources_found`: two independent sources support the candidate.
- `authoritative_source_found`: one official source of record supports it.
- `needs_second_source`: useful candidate, not enough support yet.
- `needs_reconciliation`: support exists but sources disagree on scope, date, or
  precedence.
- `needs_trust_review`: source quality, spam, or injection risk is unclear.
- `adopted_current`: safe to serve as current context.
- `adopted_with_history`: safe to serve with provenance/supersession history.
- `rejected`: false, spam, irrelevant, or unsupported after search.
- `superseded`: replaced by newer or higher-authority context.

Each transition should append an event:

```json
{
  "fact_id": "fact-...",
  "from_state": "one_source_found",
  "to_state": "needs_second_source",
  "reason": "only one credible source found",
  "source_count": 1,
  "supporting_sources": ["source-..."],
  "queued_tasks": ["verify.second_source.find"],
  "created_at": "2026-05-31T00:00:00Z"
}
```

The state history should drive queue priority:

- a one-source fact found yesterday gets a scheduled second-source search;
- a one-source fact repeatedly retrieved by agents gets higher priority;
- a high-risk or customer-impacting fact gets a faster retry cadence;
- a fact with failed source searches gets downgraded or routed to Hermes;
- an authoritative-source fact can skip the second-source requirement but still
  needs archive/trust/freshness metadata.

This gives Baltor a useful memory: "we found this yesterday, but it still needs
corroboration."

The shared schema definitions live in `_repos/shared-backend-components/schemas/_common.schema.json`; the
operational fact shape lives in `_repos/shared-backend-components/schemas/fact-record.schema.json`. Other objects
that can trigger follow-up work should use the same fields:

- `state`
- `state_history`
- `priority`
- `priority_signals`
- `queue_policy`

This keeps source records, facts, normalized objects, entities, labels,
dimensions, review tickets, jobs, and research tasks consistent.

## Source Roles

Use explicit source roles:

- `customer_original`
- `customer_current`
- `official_authority`
- `public_register`
- `publisher_primary`
- `credible_secondary`
- `news_report`
- `low_trust_reference`
- `spam_or_injection`
- `superseded`

## Anti-Injection And Spam Checks

Every fetched source should be screened for:

- prompt injection language
- hidden text or suspicious markup
- irrelevant keyword stuffing
- copied/scraped spam content
- suspicious redirects
- domain impersonation
- page content that changed during the run
- unsupported claims with no source trail
- instructions aimed at the agent rather than human readers

Injection or spam signals do not always discard the page, but they lower trust
and can force a different source or manual confirmation.

## Publisher Trust Evaluation

Use deterministic signals first:

- domain age and stability when available
- official domain pattern
- HTTPS and canonical URL
- author/publisher identity
- cited primary sources
- update timestamp
- history of prior accepted facts
- consistency with known authorities
- archive availability

LLMs can then summarize trustworthiness, but must cite the deterministic signals
they used. The LLM trust score is advisory, not a promotion gate by itself.

## Archive Queue

For promoted or high-impact facts, enqueue archive capture:

- submit URL to an archive service when allowed;
- store capture request timestamp;
- store returned archive URL or failure reason;
- store source content hash even if capture fails;
- retry on transient errors;
- never block urgent internal processing solely because archive capture is slow.

Archive status values:

- `not_required`
- `queued`
- `submitted`
- `captured`
- `failed_retryable`
- `failed_final`
- `blocked_by_policy`

## Evidence Packet

External research workers should emit:

```json
{
  "fact_id": "fact-...",
  "candidate_fact": "...",
  "support": [
    {
      "url": "https://...",
      "source_role": "official_authority",
      "retrieved_at": "2026-05-31T00:00:00Z",
      "content_hash": "sha256:...",
      "archive_status": "queued",
      "trust_score": 0.92,
      "evidence_span": "short allowed excerpt or structured field"
    }
  ],
  "adoption": {
    "status": "promote|hold|needs_more_sources|needs_reconciliation|reject",
    "reason": "two independent sources agree",
    "refresh_policy": "weekly"
  }
}
```

## Queueing Best Practice

When a worker cannot promote a fact immediately, it should enqueue the next
specific task:

- `source.archive.submit`
- `source.trust.score`
- `web.fetch.one`
- `web.site.search`
- `verify.second_source.find`
- `verify.official_source.find`
- `context.reconcile.claims`
- `openclaw.adversarial.review`
- `human.owner.confirm`

Avoid generic "review needed" when a more specific worker can continue.

Queue priority is resolved from evidence and usage signals, not from worker
opinion alone. A one-source fact with high risk, high agent usage, or old
freshness age gets requeued before low-impact background refreshes. A suspicious
source is routed to trust/adversarial review before its claims can promote.

See `baltor-stateless-worker-standard.md` (the **Queue lanes**, **Priority
signals and default policy**, and **Task routing rules** sections) for the shared
lanes, priority signals, and default task-routing policy.

## Serving Rule

Served context must be able to answer:

- What is the current fact?
- Why did Baltor adopt it?
- Which sources support it?
- What original customer fact did it supersede or preserve?
- When was it last checked?
- What will refresh it?
- What was held back and why?

Agents should usually receive `current_only` or `current_with_sources`. Admin,
audit, and high-risk workflows can request full provenance history.
