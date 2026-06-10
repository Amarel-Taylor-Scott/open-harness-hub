# Billing runbook (STALE — superseded by ADR-014)

> Last reviewed: 2025-11-02. This page predates ADR-014 and has **not** been updated.

## Retry policy

The payment-submit client retries up to **3 times** on transient failures.

<!--
DEMO NOTE: this "3" is deliberately stale and WRONG. ADR-014 (2026-03-18) set the authoritative
ceiling to 5, and repo/billing/retry.py implements 5. Baltor must detect that this runbook
CONTRADICTS the ADR + code, mark it stale, pick the ADR as the authority, and route a fix to the
owning team — instead of silently averaging or guessing.
-->
