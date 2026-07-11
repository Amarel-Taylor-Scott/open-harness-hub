#!/usr/bin/env python3
"""Backs `processor/dosage-range-validator` (process_kind ``verify.dosage_range``).

Validate a medication order's dose against weight-/age-/renal-adjusted
ranges from an injected governed dosing corpus, flagging out-of-range orders
and citing the adjusted range that applies. Deterministic decision support
for the prescriber, never an autonomous order: the output proposes the
applicable range, it does not rewrite the order. Missing patient data needed
by the matching rule → ABSTAIN with the missing fields, never a guess.

Contract: deterministic; side_effects=read; on_error=raise.
Inputs order, patient, dose_corpus → outputs in_range, adjusted.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/clinical/dosage_range_validator.py
"""
from __future__ import annotations

import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Rule selectors a corpus entry may constrain on; the FIRST matching rule in
#: corpus order applies (the corpus is authored most-specific-first).
SELECTOR_FIELDS = ("min_age_years", "max_age_years", "min_weight_kg", "max_weight_kg",
                   "renal_impairment")

VERDICT_IN_RANGE = "in_range"
VERDICT_OUT_OF_RANGE = "out_of_range"
VERDICT_ABSTAIN = "abstain_missing_data"
VERDICT_UNCOVERED = "uncovered_drug"


def _norm(name: str) -> str:
    return " ".join(str(name).lower().split())


def _rule_matches(rule: dict[str, Any], patient: dict[str, Any]) -> tuple[bool, list[str]]:
    """(matches, missing_fields) — a rule only matches on PRESENT patient data."""
    missing: list[str] = []
    for field in SELECTOR_FIELDS:
        if field not in rule:
            continue
        if field == "renal_impairment":
            if "renal_impairment" not in patient:
                missing.append("renal_impairment")
                continue
            if bool(patient["renal_impairment"]) != bool(rule[field]):
                return False, []
        else:
            pfield = "age_years" if "age" in field else "weight_kg"
            if pfield not in patient:
                missing.append(pfield)
                continue
            value = float(patient[pfield])
            if field.startswith("min_") and value < float(rule[field]):
                return False, []
            if field.startswith("max_") and value > float(rule[field]):
                return False, []
    return (not missing), missing


def run(*, order: dict[str, Any], patient: dict[str, Any],
        dose_corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate ``order`` ({"drug","dose","unit"}) for ``patient`` via the corpus.

    Corpus entries: {"drug", "unit", "low", "high", "citation", optional
    selectors (min/max age/weight, renal_impairment), optional "per_kg": true
    — then low/high are per-kg and the patient's weight is required}.
    """
    if not isinstance(order, dict) or not all(k in order for k in ("drug", "dose", "unit")):
        raise TypeError("order must be a dict with drug, dose, unit")
    if not isinstance(patient, dict):
        raise TypeError("patient must be a dict")
    if not isinstance(dose_corpus, list):
        raise TypeError("dose_corpus must be a list")
    drug = _norm(order["drug"])
    candidates = [r for r in dose_corpus
                  if isinstance(r, dict) and _norm(r.get("drug", "")) == drug]
    if not candidates:
        return {"in_range": {"verdict": VERDICT_UNCOVERED,
                             "note": "drug not in the governed dosing corpus — NOT assumed safe",
                             "disposition": "proposed", "serves_truth": False},
                "adjusted": None}
    abstain_missing: list[str] = []
    for rule in candidates:
        if not all(k in rule for k in ("unit", "low", "high", "citation")):
            raise ValueError(f"dose rule for {order['drug']!r} needs unit, low, high, citation")
        matches, missing = _rule_matches(rule, patient)
        if missing:
            abstain_missing.extend(missing)
            continue
        if not matches:
            continue
        if _norm(order["unit"]) != _norm(rule["unit"]):
            raise ValueError(f"unit mismatch: order in {order['unit']!r}, "
                             f"rule in {rule['unit']!r} — refusing to compare across units")
        low, high = float(rule["low"]), float(rule["high"])
        if rule.get("per_kg"):
            if "weight_kg" not in patient:
                abstain_missing.append("weight_kg")
                continue
            weight = float(patient["weight_kg"])
            low, high = low * weight, high * weight
        dose = float(order["dose"])
        in_range = low <= dose <= high
        return {"in_range": {"verdict": VERDICT_IN_RANGE if in_range else VERDICT_OUT_OF_RANGE,
                             "dose": dose, "unit": order["unit"],
                             "disposition": "proposed", "serves_truth": False},
                "adjusted": {"applicable_low": low, "applicable_high": high,
                             "unit": rule["unit"], "citation": rule["citation"],
                             "selectors_applied": {k: rule[k] for k in SELECTOR_FIELDS if k in rule},
                             "per_kg": bool(rule.get("per_kg", False))}}
    if abstain_missing:
        return {"in_range": {"verdict": VERDICT_ABSTAIN,
                             "missing_fields": sorted(set(abstain_missing)),
                             "note": "matching rule needs patient data that is not documented — refusing to guess",
                             "disposition": "proposed", "serves_truth": False},
                "adjusted": None}
    return {"in_range": {"verdict": VERDICT_UNCOVERED,
                         "note": "no corpus rule matches this patient — NOT assumed safe",
                         "disposition": "proposed", "serves_truth": False},
            "adjusted": None}


def _selftest() -> None:
    # SYNTHETIC demo corpus — proves the mechanism, not clinical reference data.
    corpus = [
        {"drug": "renamycin", "unit": "mg", "low": 5, "high": 7, "per_kg": True,
         "renal_impairment": True, "citation": "demo-dose:rena-renal@v1"},
        {"drug": "renamycin", "unit": "mg", "low": 10, "high": 15, "per_kg": True,
         "citation": "demo-dose:rena-standard@v1"},
    ]
    adult = {"age_years": 40, "weight_kg": 70, "renal_impairment": False}
    # Standard rule applies (renal rule selector mismatches), per-kg range computed.
    ok = run(order={"drug": "Renamycin", "dose": 800, "unit": "mg"},
             patient=adult, dose_corpus=corpus)
    assert ok["in_range"]["verdict"] == VERDICT_IN_RANGE
    assert ok["adjusted"]["applicable_low"] == 700 and ok["adjusted"]["applicable_high"] == 1050
    assert ok["adjusted"]["citation"] == "demo-dose:rena-standard@v1"
    # Renal patient hits the adjusted (most-specific-first) rule; the same dose
    # is now OUT of range and the citation says why.
    renal = run(order={"drug": "renamycin", "dose": 800, "unit": "mg"},
                patient={**adult, "renal_impairment": True}, dose_corpus=corpus)
    assert renal["in_range"]["verdict"] == VERDICT_OUT_OF_RANGE
    assert renal["adjusted"]["citation"] == "demo-dose:rena-renal@v1"
    assert renal["adjusted"]["applicable_high"] == 490
    # Missing data the rule needs → ABSTAIN naming the fields, never a guess.
    sparse = run(order={"drug": "renamycin", "dose": 800, "unit": "mg"},
                 patient={"age_years": 40}, dose_corpus=corpus)
    assert sparse["in_range"]["verdict"] == VERDICT_ABSTAIN
    assert "weight_kg" in sparse["in_range"]["missing_fields"]
    # Uncovered drug is an honest unknown.
    unk = run(order={"drug": "mysterymycin", "dose": 1, "unit": "mg"},
              patient=adult, dose_corpus=corpus)
    assert unk["in_range"]["verdict"] == VERDICT_UNCOVERED
    # Unit mismatch refuses; propose-never-dispose pinned; deterministic.
    raised = False
    try:
        run(order={"drug": "renamycin", "dose": 1, "unit": "mcg"}, patient=adult,
            dose_corpus=corpus)
    except ValueError as e:
        raised = "unit mismatch" in str(e)
    assert raised
    assert ok["in_range"]["disposition"] == "proposed" and ok["in_range"]["serves_truth"] is False
    assert json.dumps(run(order={"drug": "renamycin", "dose": 800, "unit": "mg"},
                          patient=adult, dose_corpus=corpus), sort_keys=True) == \
           json.dumps(run(order={"drug": "renamycin", "dose": 800, "unit": "mg"},
                          patient=adult, dose_corpus=corpus), sort_keys=True)
    print("PASS — dosage_range_validator: weight/renal-adjusted governed ranges with "
          "citations (most-specific-first), per-kg computation, abstain-on-missing-data, "
          "uncovered honest, unit mismatch refuses, proposed-never-disposed verified")


if __name__ == "__main__":
    _selftest()
