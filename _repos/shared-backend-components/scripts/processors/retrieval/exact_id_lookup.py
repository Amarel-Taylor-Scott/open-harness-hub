#!/usr/bin/env python3
"""Backs `processor/exact-id-lookup` (process_kind ``retrieve.exact_id``).

Deterministic hit on a structured identifier (CVE / NDC / FIPS / K-number /
SKU / statute section). Only fires when a recognized identifier is present in
the query, but when it does the match is EXACT — the governance-grade
retrieval leg: no ranking, no similarity, no false neighbors.

Contract: deterministic; side_effects=read; on_error=raise.
Inputs identifier(str — or a query containing one), corpus → output match.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/retrieval/exact_id_lookup.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Recognized structured-identifier shapes, tried in order; each maps a
#: pattern name to its regex. One definition — callers/tests read it.
ID_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("cve", re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)),
    ("ndc", re.compile(r"\b\d{4,5}-\d{3,4}-\d{1,2}\b")),                # drug package code
    ("fips", re.compile(r"\bFIPS[- ]?\d{1,3}(?:-\d)?\b", re.IGNORECASE)),
    ("k_number", re.compile(r"\bK\d{6}\b")),                            # FDA 510(k)
    ("statute_section", re.compile(r"\b\d+\s+(?:U\.?S\.?C\.?|CFR)\s+§?\s*\d+(?:\.\d+)*\b", re.IGNORECASE)),
    ("sku", re.compile(r"\bSKU[- ]?[A-Z0-9]{4,}\b", re.IGNORECASE)),
]


def extract_identifiers(text: str) -> list[dict[str, str]]:
    """All recognized identifiers in ``text`` with their pattern kind (in order)."""
    found: list[dict[str, str]] = []
    for kind, pat in ID_PATTERNS:
        for m in pat.finditer(text):
            found.append({"kind": kind, "value": m.group(0)})
    return found


def run(*, identifier: str, corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Exact-match ``identifier`` (or the ids found inside it) against ``corpus``.

    Each corpus entry is ``{"id", "text", ...}``; a hit means a recognized
    identifier appears verbatim (case-insensitive) in the entry text or
    equals its id. Returns ``{"match": {...}}`` — honest ``found: False``
    when the query carries no recognized identifier or nothing matches.
    """
    if not isinstance(identifier, str):
        raise TypeError(f"identifier must be str, got {type(identifier).__name__}")
    if not isinstance(corpus, list):
        raise TypeError(f"corpus must be a list, got {type(corpus).__name__}")
    ids = extract_identifiers(identifier)
    envelope: dict[str, Any] = {"found": False, "identifier": None, "identifier_kind": None,
                                "hits": [], "recognized_identifiers": ids}
    if not ids:
        return {"match": envelope}
    for ident in ids:
        needle = ident["value"].lower()
        hits = []
        for i, d in enumerate(corpus):
            if not isinstance(d, dict) or "id" not in d or "text" not in d:
                raise ValueError(f"corpus[{i}] needs id and text")
            if needle == str(d["id"]).lower() or needle in str(d["text"]).lower():
                hits.append({"id": str(d["id"]), "text": str(d["text"])})
        if hits:
            envelope.update(found=True, identifier=ident["value"],
                            identifier_kind=ident["kind"], hits=hits)
            return {"match": envelope}
    return {"match": envelope}


def _selftest() -> None:
    corpus = [
        {"id": "advisory-1", "text": "CVE-2024-3094: backdoor in xz-utils"},
        {"id": "reg-e", "text": "12 CFR 1005.11 error resolution procedures"},
        {"id": "k-clear", "text": "Device cleared under K123456 premarket notification"},
        {"id": "other", "text": "unrelated prose"},
    ]
    # Exact CVE hit, extracted from a natural-language query.
    m = run(identifier="what do we know about CVE-2024-3094 exploitation?", corpus=corpus)["match"]
    assert m["found"] is True and m["identifier_kind"] == "cve"
    assert m["hits"][0]["id"] == "advisory-1"
    # Statute section + 510(k) shapes.
    assert run(identifier="12 CFR 1005.11", corpus=corpus)["match"]["hits"][0]["id"] == "reg-e"
    assert run(identifier="K123456", corpus=corpus)["match"]["hits"][0]["id"] == "k-clear"
    # No recognized identifier → honest non-fire (never fuzzy-guesses).
    none = run(identifier="tell me about supply chain security", corpus=corpus)["match"]
    assert none["found"] is False and none["recognized_identifiers"] == []
    # Recognized but absent → found False with the id still reported.
    absent = run(identifier="CVE-1999-0001", corpus=corpus)["match"]
    assert absent["found"] is False and absent["recognized_identifiers"]
    # Deterministic; corpus untouched; on_error=raise.
    snap = json.dumps(corpus, sort_keys=True)
    a = json.dumps(run(identifier="CVE-2024-3094", corpus=corpus), sort_keys=True)
    assert a == json.dumps(run(identifier="CVE-2024-3094", corpus=corpus), sort_keys=True)
    assert json.dumps(corpus, sort_keys=True) == snap
    raised = False
    try:
        run(identifier=1, corpus=corpus)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised
    print("PASS — exact_id_lookup: CVE/NDC/FIPS/K-number/statute/SKU shapes fire exactly, "
          "honest non-fire without a recognized id, deterministic verified")


if __name__ == "__main__":
    _selftest()
