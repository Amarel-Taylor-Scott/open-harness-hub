"""Extract / normalize phone numbers to E.164 format.

Lightweight implementation; no external deps. For production use, swap
in `phonenumbers` (Google's libphonenumber port) for accurate per-country
parsing. This template handles the common cases and is good enough for
non-critical paths.
"""
from __future__ import annotations

import re
from typing import Any

# Match common phone forms: international, hyphenated, parenthesized.
PHONE_CANDIDATE = re.compile(
    r"(?:(?:\+|00)\s*)?(?:\(?\d{1,4}\)?[\s\-.]?){2,6}\d{2,9}"
)
DIGITS = re.compile(r"\d")
KEEP = re.compile(r"[^\d+]")


def normalize(raw: str, default_cc: str = "+1") -> str:
    digits = KEEP.sub("", raw)
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    if not digits.startswith("+"):
        # Heuristic: 10 digits → assume default country (US default).
        if len(digits) == 10:
            digits = default_cc + digits
        elif len(digits) > 10:
            digits = "+" + digits
    return digits


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    text = inputs.get("text", "")
    default_cc = inputs.get("default_country_code", "+1")
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")

    candidates = PHONE_CANDIDATE.findall(text)
    seen: set[str] = set()
    out: list[str] = []
    for c in candidates:
        digit_count = len(DIGITS.findall(c))
        if not (7 <= digit_count <= 15):
            continue
        normalized = normalize(c, default_cc)
        # E.164: + and 8-15 digits total.
        if normalized.startswith("+") and 8 <= len(normalized) - 1 <= 15 and normalized not in seen:
            seen.add(normalized)
            out.append(normalized)

    return {"phones_e164": out, "count": len(out)}
