"""Parse common date formats and normalize to ISO 8601 (YYYY-MM-DD).

Lightweight; no external deps. Handles the common formats. For production
use `dateutil.parser` or `pendulum` for richer parsing.
"""
from __future__ import annotations

import datetime as _dt
import re
from typing import Any

# Try these patterns in order. Each captures (year, month, day) or
# uses datetime.strptime.
PATTERNS = [
    ("%Y-%m-%d",   re.compile(r"^\d{4}-\d{1,2}-\d{1,2}$")),
    ("%Y/%m/%d",   re.compile(r"^\d{4}/\d{1,2}/\d{1,2}$")),
    ("%d/%m/%Y",   re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")),
    ("%d-%m-%Y",   re.compile(r"^\d{1,2}-\d{1,2}-\d{4}$")),
    ("%B %d, %Y",  re.compile(r"^[A-Za-z]+ \d{1,2}, \d{4}$")),
    ("%d %B %Y",   re.compile(r"^\d{1,2} [A-Za-z]+ \d{4}$")),
    ("%Y%m%d",     re.compile(r"^\d{8}$")),
]


def parse_one(raw: str) -> str | None:
    raw = raw.strip()
    if not raw:
        return None
    for fmt, regex in PATTERNS:
        if regex.match(raw):
            try:
                return _dt.datetime.strptime(raw, fmt).date().isoformat()
            except ValueError:
                continue
    return None


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("date", "")
    if not isinstance(raw, str):
        raise TypeError(f"date must be str, got {type(raw).__name__}")
    iso = parse_one(raw)
    return {"input": raw, "iso8601": iso, "ok": iso is not None}
