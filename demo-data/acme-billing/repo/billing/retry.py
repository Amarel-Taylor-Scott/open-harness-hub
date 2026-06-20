"""Acme billing — payment-submit retry client (synthetic demo code).

Implements ADR-014: at most 5 retries, full-jitter exponential backoff, retry-safe codes only.
"""
from __future__ import annotations

# Per ADR-014 (Billing retry policy). The runbook's "3" is stale; this is the implemented ceiling.
MAX_RETRIES = 5
BACKOFF_BASE_MS = 200
BACKOFF_CAP_MS = 20_000
RETRY_SAFE_STATUS = (429, 502, 503, 504)


def should_retry(status_code: int, attempt: int) -> bool:
    """True iff this status is retry-safe and we are still under the ADR-014 ceiling."""
    return status_code in RETRY_SAFE_STATUS and attempt < MAX_RETRIES
