#!/usr/bin/env python3
"""Backs `processor/allergy-contraindication-check` (process_kind ``verify.allergy_contraindication``).

Check ordered medications/procedures against the patient's DOCUMENTED
allergies and contraindicated conditions, using an injected governed
contraindication corpus (drug↔allergy-class and drug↔condition rules with
citations). Deterministic: a conflict BLOCKS the order and routes to review
with the documented source; an order with no documented allergy/condition
match passes WITH the caveat that documentation completeness is the
clinician's domain.

Contract: deterministic; side_effects=read; on_error=raise.
Inputs orders, allergies, conditions → output conflicts.

CLI / self-test: python3 scripts/processors/clinical/allergy_contraindication_check.py
"""
from __future__ import annotations

import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

CONFLICT_ALLERGY = "allergy"
CONFLICT_CONDITION = "condition"

#: Action on conflict (single definition; the order pipeline reads it).
CONFLICT_ACTION = "block_order_and_route_to_review"


def _norm(name: str) -> str:
    return " ".join(str(name).lower().split())


def run(*, orders: list[str], allergies: list[str], conditions: list[str],
        contraindication_corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Check every order against documented allergies/conditions via the corpus.

    Corpus entries: {"order", "kind": "allergy"|"condition", "match"
    (the allergy class or condition it conflicts with), "reason", "citation"}.
    """
    for nm, v in (("orders", orders), ("allergies", allergies), ("conditions", conditions)):
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise TypeError(f"{nm} must be a list of strings")
    if not isinstance(contraindication_corpus, list):
        raise TypeError("contraindication_corpus must be a list")
    rules: list[dict[str, Any]] = []
    for i, r in enumerate(contraindication_corpus):
        if not isinstance(r, dict) or not all(k in r for k in ("order", "kind", "match", "reason", "citation")):
            raise ValueError(f"contraindication_corpus[{i}] needs order, kind, match, reason, citation")
        if r["kind"] not in (CONFLICT_ALLERGY, CONFLICT_CONDITION):
            raise ValueError(f"contraindication_corpus[{i}] kind {r['kind']!r} unknown")
        rules.append(r)

    doc_allergies = {_norm(a) for a in allergies}
    doc_conditions = {_norm(c) for c in conditions}
    hits: list[dict[str, Any]] = []
    cleared: list[str] = []
    for order in orders:
        order_n = _norm(order)
        order_hits = []
        for r in rules:
            if _norm(r["order"]) != order_n:
                continue
            documented = doc_allergies if r["kind"] == CONFLICT_ALLERGY else doc_conditions
            if _norm(r["match"]) in documented:
                order_hits.append({"order": order, "kind": r["kind"],
                                   "documented_match": r["match"], "reason": r["reason"],
                                   "citation": r["citation"], "action": CONFLICT_ACTION})
        if order_hits:
            hits.extend(order_hits)
        else:
            cleared.append(order)
    return {"conflicts": {
        "hits": sorted(hits, key=lambda h: (h["order"], h["kind"], h["documented_match"])),
        "cleared_orders": cleared,
        "cleared_caveat": ("cleared = no documented allergy/condition matched a corpus rule; "
                           "documentation completeness is the clinician's call"),
        "disposition": "proposed", "serves_truth": False,
    }}


def _selftest() -> None:
    # SYNTHETIC demo corpus — proves the mechanism, not clinical reference data.
    corpus = [
        {"order": "amoxicillin", "kind": "allergy", "match": "penicillin",
         "reason": "beta-lactam cross-reactivity", "citation": "demo-ci:amox-pcn@v1"},
        {"order": "ibuprofen", "kind": "condition", "match": "chronic kidney disease",
         "reason": "NSAID nephrotoxicity in CKD", "citation": "demo-ci:nsaid-ckd@v1"},
        {"order": "ibuprofen", "kind": "allergy", "match": "aspirin",
         "reason": "NSAID class cross-reactivity", "citation": "demo-ci:nsaid-asa@v1"},
    ]
    out = run(orders=["Amoxicillin", "Ibuprofen", "Acetaminophen"],
              allergies=["Penicillin"], conditions=["Chronic Kidney Disease"],
              contraindication_corpus=corpus)["conflicts"]
    # Both documented conflicts fire with their citations and block.
    assert len(out["hits"]) == 2
    amox = next(h for h in out["hits"] if h["order"] == "Amoxicillin")
    assert amox["kind"] == CONFLICT_ALLERGY and amox["citation"] == "demo-ci:amox-pcn@v1"
    ibu = next(h for h in out["hits"] if h["order"] == "Ibuprofen")
    assert ibu["kind"] == CONFLICT_CONDITION and ibu["action"] == CONFLICT_ACTION
    # The aspirin rule does NOT fire (aspirin allergy not documented) — rules
    # fire on DOCUMENTED matches only, never on speculation.
    assert all(h["documented_match"] != "aspirin" for h in out["hits"])
    # Unmatched order clears WITH the documentation caveat.
    assert out["cleared_orders"] == ["Acetaminophen"] and "clinician" in out["cleared_caveat"]
    # No documented allergies/conditions → everything clears (nothing invented).
    clean = run(orders=["amoxicillin"], allergies=[], conditions=[],
                contraindication_corpus=corpus)["conflicts"]
    assert clean["hits"] == [] and clean["cleared_orders"] == ["amoxicillin"]
    # Propose-never-dispose pinned; deterministic; on_error=raise.
    assert out["disposition"] == "proposed" and out["serves_truth"] is False
    a = json.dumps(run(orders=["ibuprofen"], allergies=["aspirin"], conditions=[],
                       contraindication_corpus=corpus), sort_keys=True)
    b = json.dumps(run(orders=["ibuprofen"], allergies=["aspirin"], conditions=[],
                       contraindication_corpus=corpus), sort_keys=True)
    assert a == b
    raised = False
    try:
        run(orders=["x"], allergies=[], conditions=[],
            contraindication_corpus=[{"order": "x", "kind": "vibes", "match": "m",
                                      "reason": "r", "citation": "c"}])
    except ValueError:
        raised = True
    assert raised
    print("PASS — allergy_contraindication_check: documented-match-only conflicts with "
          "citations (allergy class + condition), block-and-review action, honest "
          "cleared caveat, proposed-never-disposed verified")


if __name__ == "__main__":
    _selftest()
