"""Validate IBANs with mod-97 checksum + per-country length."""
from __future__ import annotations

import re
from typing import Any

# Country -> expected total length. Subset; expand as needed.
IBAN_LENGTHS = {
    "AD": 24, "AE": 23, "AL": 28, "AT": 20, "AZ": 28, "BA": 20, "BE": 16,
    "BG": 22, "BH": 22, "BR": 29, "CH": 21, "CR": 22, "CY": 28, "CZ": 24,
    "DE": 22, "DK": 18, "DO": 28, "EE": 20, "EG": 29, "ES": 24, "FI": 18,
    "FO": 18, "FR": 27, "GB": 22, "GE": 22, "GI": 23, "GL": 18, "GR": 27,
    "GT": 28, "HR": 21, "HU": 28, "IE": 22, "IL": 23, "IS": 26, "IT": 27,
    "JO": 30, "KW": 30, "KZ": 20, "LB": 28, "LI": 21, "LT": 20, "LU": 20,
    "LV": 21, "MC": 27, "MD": 24, "ME": 22, "MK": 19, "MR": 27, "MT": 31,
    "MU": 30, "NL": 18, "NO": 15, "PK": 24, "PL": 28, "PS": 29, "PT": 25,
    "QA": 29, "RO": 24, "RS": 22, "SA": 24, "SE": 24, "SI": 19, "SK": 24,
    "SM": 27, "TN": 24, "TR": 26, "UA": 29, "VG": 24, "XK": 20,
}

IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]+$")


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("iban", "")
    if not isinstance(raw, str):
        raise TypeError(f"expected iban: str, got {type(raw).__name__}")

    iban = raw.upper().replace(" ", "").replace("-", "")
    reasons: list[str] = []

    if not IBAN_RE.match(iban):
        reasons.append("format_invalid")
    else:
        country = iban[:2]
        if country in IBAN_LENGTHS and len(iban) != IBAN_LENGTHS[country]:
            reasons.append(f"length_invalid_for_{country}_expected_{IBAN_LENGTHS[country]}")

        # mod-97: move first 4 chars to end, convert letters to digits, mod 97 == 1
        rearranged = iban[4:] + iban[:4]
        digits = "".join(str(ord(c) - ord("A") + 10) if c.isalpha() else c for c in rearranged)
        try:
            checksum_ok = int(digits) % 97 == 1
        except ValueError:
            checksum_ok = False
        if not checksum_ok:
            reasons.append("checksum_failed")

    return {
        "iban": iban,
        "valid": len(reasons) == 0,
        "reasons": reasons,
        "country": iban[:2] if len(iban) >= 2 else None,
    }
