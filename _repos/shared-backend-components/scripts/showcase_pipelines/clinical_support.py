#!/usr/bin/env python3
"""Showcase: DEFENSIVE clinical decision-support, composing the clinical family.

Scenario: a prescriber orders for a patient on warfarin with documented CKD and a
penicillin allergy, plus a fresh potassium lab. The pipeline runs the governed
deterministic checks and PROPOSES flags / ESCALATES — it never autonomously acts,
and every envelope pins serves_truth=False (the clinical family's law).

Composition (every step a real `_repos/shared-backend-components/scripts/processors/clinical` callable):
  1. drug_interaction_checker      — pairwise lookup vs a governed interaction corpus
  2. allergy_contraindication_check — documented allergy/condition conflicts
  3. dosage_range_validator        — weight/renal-adjusted range with citation
  4. lab_critical_value_flag       — panic-value escalation
  5. clinical_abstention_gate      — block an answer the evidence can't support
  6. escalate_human                — the governed escalation when anything fires

Run:  python3 _repos/shared-backend-components/scripts/showcase_pipelines/clinical_support.py [--self-test]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.processors.clinical.allergy_contraindication_check import run as allergy_run
from scripts.processors.clinical.clinical_abstention_gate import run as abstain_run
from scripts.processors.clinical.dosage_range_validator import run as dose_run
from scripts.processors.clinical.drug_interaction_checker import run as interaction_run
from scripts.processors.clinical.lab_critical_value_flag import run as lab_run
from scripts.processors.deliver.escalate_human import run as escalate_run

# SYNTHETIC governed reference corpora — prove the mechanism, NOT clinical reference data.
_INTERACTIONS = [
    {"drug_a": "warfarin", "drug_b": "fluconazole", "severity": "major",
     "mechanism": "CYP2C9 inhibition raises INR", "citation": "demo-ddi:wf-flu@v1"},
]
_CONTRAINDICATIONS = [
    {"order": "ibuprofen", "kind": "condition", "match": "chronic kidney disease",
     "reason": "NSAID nephrotoxicity in CKD", "citation": "demo-ci:nsaid-ckd@v1"},
    {"order": "amoxicillin", "kind": "allergy", "match": "penicillin",
     "reason": "beta-lactam cross-reactivity", "citation": "demo-ci:amox-pcn@v1"},
]
_DOSE_CORPUS = [
    {"drug": "warfarin", "unit": "mg", "low": 2, "high": 10, "citation": "demo-dose:wf@v1"},
]
_LAB_RANGES = [
    {"analyte": "potassium", "unit": "mmol/L", "normal_low": 3.5, "normal_high": 5.0,
     "critical_low": 2.5, "critical_high": 6.5, "citation": "demo-ranges:k@v1"},
]


def run(*, patient: dict[str, Any], orders: list[dict[str, Any]],
        labs: list[dict[str, Any]]) -> dict[str, Any]:
    """Run the defensive clinical checks; PROPOSE flags + ESCALATE. Never autonomous."""
    findings: list[dict[str, Any]] = []
    queue: list[dict[str, Any]] = []

    def _enqueue(ticket):  # an in-memory review queue stands in for the real one
        queue.append(ticket)
        return {"ref": f"q-{len(queue):04d}"}

    med_names = [o["drug"] for o in orders if "drug" in o]
    # 1. interactions
    ix = interaction_run(med_list=med_names + patient.get("current_meds", []),
                         interaction_corpus=_INTERACTIONS)
    if ix["interactions"]["hits"]:
        findings.append({"kind": "interaction", "severity": ix["severity"],
                         "hits": ix["interactions"]["hits"]})
    # 2. allergy / contraindication
    ac = allergy_run(orders=[o["drug"] for o in orders], allergies=patient.get("allergies", []),
                     conditions=patient.get("conditions", []),
                     contraindication_corpus=_CONTRAINDICATIONS)
    if ac["conflicts"]["hits"]:
        findings.append({"kind": "contraindication", "hits": ac["conflicts"]["hits"]})
    # 3. dosing
    for o in orders:
        if all(k in o for k in ("drug", "dose", "unit")):
            dv = dose_run(order=o, patient=patient, dose_corpus=_DOSE_CORPUS)["in_range"]
            if dv["verdict"] == "out_of_range":
                findings.append({"kind": "dose_out_of_range", "order": o["drug"]})
    # 4. labs (panic values)
    lab = lab_run(labs=labs, reference_ranges=_LAB_RANGES)
    if lab["escalate"]["required"]:
        findings.append({"kind": "critical_lab", "analytes": lab["escalate"]["analytes"]})

    # 5. abstention gate on a draft summary (must be evidence-supported)
    draft = "Order set reviewed; flagged items require prescriber attention."
    suff = abstain_run(answer={"text": draft, "cited_evidence_ids": []},
                       evidence=[{"id": f["kind"], "kind": "documented_finding",
                                  "text": json.dumps(f, sort_keys=True)} for f in findings]
                       or [{"id": "none", "kind": "documented_finding", "text": "no findings"}])

    # 6. escalate when anything fired (the governed path; nothing autonomous)
    escalated = None
    if findings:
        escalated = escalate_run(result={"patient_id": patient.get("id"), "findings": findings},
                                 reason="gate_fired", enqueue=_enqueue)["ticket"]
    return {"findings": findings, "escalated": escalated is not None,
            "ticket": escalated["queue_ref"] if escalated else None,
            "draft_sufficient": suff["sufficient"],
            "disposition": "proposed", "serves_truth": False}


_PATIENT = {"id": "demo-patient-1", "weight_kg": 80, "renal_impairment": True,
            "allergies": ["Penicillin"], "conditions": ["Chronic Kidney Disease"],
            "current_meds": ["Fluconazole"]}
_ORDERS = [{"drug": "Warfarin", "dose": 5, "unit": "mg"},
           {"drug": "Ibuprofen"}, {"drug": "Amoxicillin"}]
_LABS = [{"analyte": "Potassium", "value": 6.8, "unit": "mmol/L"}]


def _self_test() -> int:
    out = run(patient=_PATIENT, orders=_ORDERS, labs=_LABS)
    kinds = {f["kind"] for f in out["findings"]}
    # Every governed check fired on this deliberately-loaded case.
    assert "interaction" in kinds          # warfarin × fluconazole
    assert "contraindication" in kinds     # ibuprofen+CKD, amoxicillin+penicillin
    assert "critical_lab" in kinds         # K+ 6.8 panic value
    # It ESCALATED and never acted autonomously.
    assert out["escalated"] is True and out["ticket"]
    assert out["disposition"] == "proposed" and out["serves_truth"] is False
    # A clean patient produces no escalation.
    clean = run(patient={"id": "p2", "weight_kg": 70}, orders=[{"drug": "acetaminophen"}],
                labs=[{"analyte": "potassium", "value": 4.2, "unit": "mmol/L"}])
    assert clean["escalated"] is False
    # Deterministic.
    assert json.dumps(run(patient=_PATIENT, orders=_ORDERS, labs=_LABS), sort_keys=True) == \
           json.dumps(run(patient=_PATIENT, orders=_ORDERS, labs=_LABS), sort_keys=True)
    print("PASS — clinical_support: interaction + contraindication + panic-lab checks fired, "
          "escalated to review (never autonomous), serves_truth=False, deterministic")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Defensive clinical decision-support showcase.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    print(json.dumps(run(patient=_PATIENT, orders=_ORDERS, labs=_LABS), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
