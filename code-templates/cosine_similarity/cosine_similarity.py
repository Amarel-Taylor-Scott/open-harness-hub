"""Cosine similarity between two equal-length vectors.

No NumPy dep — pure Python. For batch operations with NumPy add
a separate processor.
"""
from __future__ import annotations

import math
from typing import Any


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    a = inputs.get("a", [])
    b = inputs.get("b", [])
    if not (isinstance(a, list) and isinstance(b, list)):
        raise TypeError("a and b must be lists of floats")
    if len(a) != len(b):
        raise ValueError(f"length mismatch: {len(a)} vs {len(b)}")
    if not a:
        return {"score": 0.0, "dim": 0}
    dot = sum(float(x) * float(y) for x, y in zip(a, b))
    na  = math.sqrt(sum(float(x) * float(x) for x in a))
    nb  = math.sqrt(sum(float(y) * float(y) for y in b))
    if na == 0.0 or nb == 0.0:
        return {"score": 0.0, "dim": len(a)}
    return {"score": dot / (na * nb), "dim": len(a)}
