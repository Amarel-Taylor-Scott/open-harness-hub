"""field_ontology — canonicalize surface field names to one canonical id (backs registry #20 semantic_ontology).

Extraction + linking should treat `invoice_number`, `Invoice No.`, `bill_number` as ONE field. This loads
architecture/semantic_field_ontology.json and resolves any surface name -> its canonical id deterministically
(normalize then alias-match). LLM disambiguation is only for novel names this map doesn't cover.

Complements entity_resolver (which normalizes VALUES); this normalizes FIELD NAMES. serves_truth=false.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]          # src/teleon/resolution/ -> repo root
_ONTOLOGY = _REPO / "architecture" / "semantic_field_ontology.json"
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize(name: str) -> str:
    """lowercase; non-alphanumeric runs -> '_'; strip leading/trailing '_'."""
    return _NON_ALNUM.sub("_", str(name).lower()).strip("_")


@lru_cache(maxsize=1)
def _alias_index() -> dict[str, str]:
    """normalized surface name -> canonical id (canonical itself + every alias)."""
    fields = json.loads(_ONTOLOGY.read_text()).get("fields", [])
    idx: dict[str, str] = {}
    for f in fields:
        canon = f["canonical"]
        for surface in [canon, *f.get("aliases", [])]:
            idx[normalize(surface)] = canon
    return idx


def canonicalize(field_name: str) -> str | None:
    """Surface field name -> canonical id, or None if unknown (caller may escalate to the LLM)."""
    return _alias_index().get(normalize(field_name))


def aliases_of(canonical: str) -> list[str]:
    fields = json.loads(_ONTOLOGY.read_text()).get("fields", [])
    for f in fields:
        if f["canonical"] == canonical:
            return list(f.get("aliases", []))
    return []
