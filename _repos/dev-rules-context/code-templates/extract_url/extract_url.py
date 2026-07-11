"""Extract HTTP(S) URLs from text."""
from __future__ import annotations

import re
from typing import Any

URL_RE = re.compile(r"https?://[^\s<>\"'`]+", re.IGNORECASE)


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    text = inputs.get("text", "")
    if not isinstance(text, str):
        raise TypeError(f"expected text: str, got {type(text).__name__}")

    found = URL_RE.findall(text)
    # Strip common trailing punctuation that shouldn't be part of the URL.
    cleaned = [u.rstrip(",.;:!?)]}>'\"") for u in found]
    seen: set[str] = set()
    urls: list[str] = []
    for u in cleaned:
        if u and u not in seen:
            seen.add(u)
            urls.append(u)
    return {"urls": urls, "count": len(urls)}
