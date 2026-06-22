"""io_contracts — typed I/O contracts per tool-plane (the Haystack/Langflow pre-runtime type-check, grounded in our
shared-I/O spine). Single source: architecture/plane_io_contracts.json. The compiler uses edge_compatible() to surface
DAG edges that connect incompatible types (a producer whose output type no consumer input accepts) BEFORE running —
the same guarantee Haystack gives by typing component ports. serves_truth=false (this types the flow, it doesn't judge truth).

Coverage is partial-but-grounded (the composing planes); an edge touching an UNCOVERED plane is treated as compatible
(unknown, not penalized) so the check never blocks on a plane we haven't typed yet.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_CONTRACTS = Path(__file__).resolve().parents[3] / "architecture" / "plane_io_contracts.json"


@lru_cache(maxsize=1)
def load_contracts() -> dict:
    return json.loads(_CONTRACTS.read_text())


def plane_io(plane: str | None) -> dict | None:
    """The {consumes, produces} contract for a plane, or None if the plane is not (yet) typed."""
    if not plane:
        return None
    return load_contracts().get("planes", {}).get(plane)


def edge_compatible(producer_plane: str | None, consumer_plane: str | None) -> bool:
    """True iff the producer can feed the consumer: producer.produces ∩ consumer.consumes ≠ ∅. An edge touching an
    UNCOVERED plane is compatible (unknown, never penalized). This is the pre-runtime type-check Haystack does on ports."""
    p, c = plane_io(producer_plane), plane_io(consumer_plane)
    if p is None or c is None:
        return True                                   # at least one plane isn't typed yet -> don't block
    return bool(set(p.get("produces", [])) & set(c.get("consumes", [])))
