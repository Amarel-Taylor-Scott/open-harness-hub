"""Extract email addresses from text — RFC-5322-lite.

Contract: see input.schema.json / output.schema.json.
Token cost: 0 (deterministic regex).
"""
from __future__ import annotations

import re
from typing import Any

# RFC-5322-lite — practical pattern used by gitleaks, Presidio, Yelp/detect-secrets.
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Extract unique email addresses from `text`.

    Args:
        inputs: { "text": str }

    Returns:
        { "emails": list[str], "count": int }
    """
    text = inputs.get("text", "")
    if not isinstance(text, str):
        raise TypeError(f"expected text: str, got {type(text).__name__}")

    found = EMAIL_RE.findall(text)
    # Preserve order while dedup.
    seen: set[str] = set()
    emails: list[str] = []
    for e in found:
        e_lower = e.lower()
        if e_lower not in seen:
            seen.add(e_lower)
            emails.append(e)

    return {"emails": emails, "count": len(emails)}


if __name__ == "__main__":
    # Manual smoke test
    import json, sys
    sample = sys.stdin.read() or "Contact me at alice@example.com or bob@test.org. Repeat alice@example.com."
    print(json.dumps(run({"text": sample}), indent=2))
