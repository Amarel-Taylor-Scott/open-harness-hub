"""SHA-256 hex digest — for audit trails, content-addressable storage, dedup."""
from __future__ import annotations

import hashlib
from typing import Any


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    payload = inputs.get("payload", "")
    encoding = inputs.get("encoding", "utf-8")
    if isinstance(payload, str):
        data = payload.encode(encoding)
    elif isinstance(payload, (bytes, bytearray)):
        data = bytes(payload)
    else:
        raise TypeError(f"payload must be str or bytes, got {type(payload).__name__}")
    h = hashlib.sha256(data)
    return {
        "sha256": h.hexdigest(),
        "byte_count": len(data),
    }
