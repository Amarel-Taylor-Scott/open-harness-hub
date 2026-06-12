#!/usr/bin/env python3
"""Backs `processor/clinical-redflag-screen` (process_kind ``gate.clinical_redflag``).

Deterministic pattern screen over a clinical note + vitals for time-critical
RED-FLAG syndromes. The syndrome definitions are an INJECTED governed rule
corpus (each rule: required note findings and/or vital thresholds, with a
citation); two demo rules in the self-test show the shape (qSOFA-style
vitals rule, symptom-combination rule). On ANY fired flag the screen
ESCALATES to a clinician and FORBIDS reassurance phrasing in downstream
output — the bare model's most dangerous failure is calm confidence.

Contract: deterministic; side_effects=none; on_error=raise.
Inputs note, vitals → outputs red_flags, escalate.

CLI / self-test: python3 scripts/processors/clinical/clinical_redflag_screen.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Vital comparators a rule may use.
_COMPARATORS = {"<=": lambda a, b: a <= b, ">=": lambda a, b: a >= b,
                "<": lambda a, b: a < b, ">": lambda a, b: a > b}

#: Downstream phrasing forbidden once a flag fires (single definition; the
#: prompt layer reads it).
FORBIDDEN_REASSURANCE = ("likely nothing serious", "no need to worry", "probably fine",
                         "reassure the patient")

ESCALATE_ACTION = "escalate to clinician NOW (time-critical screen fired)"


def _norm(text: str) -> str:
    return " ".join(str(text).lower().split())


def run(*, note: str, vitals: dict[str, float],
        redflag_corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Screen ``note`` + ``vitals`` against the injected red-flag rule corpus.

    Rule shape: {"syndrome", "citation", "note_findings_all"?: [str] (every
    phrase must appear), "note_findings_any"?: [str] (at least one),
    "vital_criteria"?: [{"vital", "comparator", "value"}], "min_criteria"?:
    int (of the vital criteria; default all)}.
    """
    if not isinstance(note, str):
        raise TypeError("note must be str")
    if not isinstance(vitals, dict):
        raise TypeError("vitals must be a dict of vital -> number")
    if not isinstance(redflag_corpus, list):
        raise TypeError("redflag_corpus must be a list of rules")
    note_n = _norm(note)
    fired: list[dict[str, Any]] = []
    for i, rule in enumerate(redflag_corpus):
        if not isinstance(rule, dict) or "syndrome" not in rule or "citation" not in rule:
            raise ValueError(f"redflag_corpus[{i}] needs syndrome and citation")
        evidence: list[str] = []
        ok = True
        for phrase in rule.get("note_findings_all", []):
            if _norm(phrase) in note_n:
                evidence.append(f"note: {phrase!r}")
            else:
                ok = False
                break
        if ok and rule.get("note_findings_any"):
            any_hits = [p for p in rule["note_findings_any"] if _norm(p) in note_n]
            if any_hits:
                evidence.extend(f"note: {p!r}" for p in any_hits)
            else:
                ok = False
        if ok and rule.get("vital_criteria"):
            met = []
            for c in rule["vital_criteria"]:
                comp = _COMPARATORS.get(c.get("comparator"))
                if comp is None:
                    raise ValueError(f"rule {rule['syndrome']!r} has unknown comparator "
                                     f"{c.get('comparator')!r}; known: {sorted(_COMPARATORS)}")
                if c["vital"] in vitals and comp(float(vitals[c["vital"]]), float(c["value"])):
                    met.append(f"vital: {c['vital']} {c['comparator']} {c['value']} "
                               f"(measured {vitals[c['vital']]})")
            need = int(rule.get("min_criteria", len(rule["vital_criteria"])))
            if len(met) >= need:
                evidence.extend(met)
            else:
                ok = False
        if ok and evidence:
            fired.append({"syndrome": rule["syndrome"], "evidence": evidence,
                          "citation": rule["citation"]})
    fired.sort(key=lambda f: f["syndrome"])
    return {"red_flags": {"fired": fired, "rules_evaluated": len(redflag_corpus),
                          "disposition": "proposed", "serves_truth": False},
            "escalate": {"required": bool(fired),
                         "action": ESCALATE_ACTION if fired else None,
                         "forbid_reassurance": bool(fired),
                         "forbidden_phrases": list(FORBIDDEN_REASSURANCE) if fired else []}}


def _selftest() -> None:
    # SYNTHETIC demo rules — they show the rule SHAPE, not clinical reference data.
    corpus = [
        {"syndrome": "sepsis-screen (qSOFA-style demo)", "citation": "demo-redflag:qsofa@v1",
         "vital_criteria": [
             {"vital": "respiratory_rate", "comparator": ">=", "value": 22},
             {"vital": "systolic_bp", "comparator": "<=", "value": 100},
             {"vital": "gcs", "comparator": "<", "value": 15}],
         "min_criteria": 2},
        {"syndrome": "acs-screen (symptom-combination demo)", "citation": "demo-redflag:acs@v1",
         "note_findings_all": ["chest pain"],
         "note_findings_any": ["radiating to the left arm", "diaphoresis", "radiating to the jaw"]},
    ]
    # Two-of-three vitals fire the qSOFA-style rule with measured evidence.
    out = run(note="patient drowsy, complains of weakness",
              vitals={"respiratory_rate": 24, "systolic_bp": 92, "gcs": 15},
              redflag_corpus=corpus)
    fired = out["red_flags"]["fired"]
    assert len(fired) == 1 and "sepsis" in fired[0]["syndrome"]
    assert any("respiratory_rate" in e for e in fired[0]["evidence"])
    assert out["escalate"]["required"] is True and out["escalate"]["forbid_reassurance"] is True
    assert "probably fine" in out["escalate"]["forbidden_phrases"]
    # Symptom combination: all + any semantics.
    acs = run(note="Severe chest pain since 0700, diaphoresis noted.",
              vitals={}, redflag_corpus=corpus)
    assert any("acs" in f["syndrome"] for f in acs["red_flags"]["fired"])
    # 'chest pain' without a qualifying ANY finding does not fire.
    calm = run(note="mild chest pain after exercise, resolved", vitals={}, redflag_corpus=corpus)
    assert calm["red_flags"]["fired"] == [] and calm["escalate"]["required"] is False
    assert calm["escalate"]["forbidden_phrases"] == []
    # Missing vitals never satisfy a criterion (no guessed measurements).
    nov = run(note="drowsy", vitals={"respiratory_rate": 24}, redflag_corpus=corpus)
    assert nov["red_flags"]["fired"] == []
    # Propose-never-dispose pinned; deterministic; on_error=raise.
    assert out["red_flags"]["disposition"] == "proposed" and out["red_flags"]["serves_truth"] is False
    assert json.dumps(run(note="x", vitals={}, redflag_corpus=corpus), sort_keys=True) == \
           json.dumps(run(note="x", vitals={}, redflag_corpus=corpus), sort_keys=True)
    raised = False
    try:
        run(note="x", vitals={}, redflag_corpus=[{"syndrome": "s", "citation": "c",
                                                  "vital_criteria": [{"vital": "v", "comparator": "~", "value": 1}]}])
    except ValueError:
        raised = True
    assert raised
    print("PASS — clinical_redflag_screen: injected rule corpus (all/any findings + "
          "min-of-N vital criteria) with measured evidence + citations, fired flags "
          "escalate NOW and forbid reassurance, missing vitals never guessed verified")


if __name__ == "__main__":
    _selftest()
