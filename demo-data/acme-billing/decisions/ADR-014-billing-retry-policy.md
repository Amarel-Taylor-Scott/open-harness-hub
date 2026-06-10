# ADR-014: Billing retry policy

- Status: Accepted
- Date: 2026-03-18
- Deciders: billing-team
- Supersedes: the retry guidance in `docs/billing-runbook.md`

## Context

After INC-2026-04 (the retry storm), the unbounded client-side retries amplified a transient
downstream outage into a self-inflicted overload. We need a single, authoritative retry policy.

## Decision

The billing payment-submit client uses **at most 5 retries** with full-jitter exponential
backoff (base 200ms, cap 20s). Retries apply only to idempotent, retry-safe status codes
(429, 502, 503, 504). 5xx that are not retry-safe and all 4xx except 429 are surfaced immediately.

> Authoritative value: **max_retries = 5**.

This decision is the source of truth for the retry ceiling. The runbook is superseded and must be
updated to match; until it is, treat the runbook's number as stale.

## Consequences

- `repo/billing/retry.py` implements `MAX_RETRIES = 5`.
- The runbook (`docs/billing-runbook.md`, which still says 3) is now stale and contradicts this ADR.
