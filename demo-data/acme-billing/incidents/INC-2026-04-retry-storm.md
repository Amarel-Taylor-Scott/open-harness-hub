# INC-2026-04: Billing retry storm

- Severity: SEV-2
- Date: 2026-03-10
- Service: billing-service

## Summary

A transient downstream outage was amplified by unbounded client retries, causing a self-inflicted
overload. Root cause: no retry ceiling and no jitter on the payment-submit path.

## Follow-up

ADR-014 was written to set an authoritative retry policy (max 5 retries, full-jitter exponential
backoff, retry-safe status codes only).
