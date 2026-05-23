"""Validate a digit string using the Luhn mod-10 checksum.

Used by credit-card PANs, IMEI numbers, NPI (US healthcare provider IDs),
Canadian SIN, and others. Strips spaces and hyphens before checksum.
"""
from __future__ import annotations

from typing import Any


def luhn_check(digits: str) -> bool:
    """Return True iff the digit string passes the Luhn mod-10 check."""
    total = 0
    flip = False
    for ch in reversed(digits):
        if not ch.isdigit():
            return False
        n = int(ch)
        if flip:
            n *= 2
            if n > 9:
                n -= 9
        total += n
        flip = not flip
    return total % 10 == 0


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("value", "")
    if not isinstance(raw, str):
        raise TypeError(f"expected value: str, got {type(raw).__name__}")

    digits = raw.replace(" ", "").replace("-", "")
    valid = bool(digits) and digits.isdigit() and luhn_check(digits)
    return {
        "value":         raw,
        "digits":        digits,
        "valid":         valid,
        "digit_count":   len(digits),
    }
