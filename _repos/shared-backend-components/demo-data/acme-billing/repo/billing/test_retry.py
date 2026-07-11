"""Test pinning the ADR-014 retry ceiling (synthetic demo)."""
from billing.retry import MAX_RETRIES, should_retry


def test_ceiling_is_five():
    assert MAX_RETRIES == 5  # ADR-014 — the authoritative ceiling


def test_stops_at_ceiling():
    assert should_retry(503, attempt=4) is True
    assert should_retry(503, attempt=5) is False


def test_non_retry_safe_codes_never_retry():
    assert should_retry(400, attempt=0) is False
