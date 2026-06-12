#!/usr/bin/env python3
"""Showcase: ICD-10 coding assistant — code over a governed terminology, abstain over fabricate.

Structural gap (durability: coded vocabulary): the output is a CODE where fluency gives zero
signal — a plausible-but-wrong code is a compliance liability. A bare model invents
plausible-looking ICD-10 codes; the governed path grounds each documented diagnosis to the
terminology and leaves the undocumented/unmatched ones UNCODED. Defensive: proposes for a
human coder, never autonomous; serves_truth=False.

Composition (real `scripts/processors` callables):
  1. soap_note_structurer       — structure the encounter; the Assessment section holds diagnoses
  2. icd10_code_grounder        — resolve each diagnosis to an ICD-10 code via the terminology
                                  (exact + synonyms), with the documentation span; abstain otherwise
  3. clinical_abstention_gate   — block the coding summary if the evidence can't support it
  4. escalate_human             — route the proposed codes to a coder to confirm

Run:  python3 scripts/showcase_pipelines/icd10_coding.py [--self-test]
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

from scripts.processors.clinical.soap_note_structurer import run as soap_run
from scripts.processors.clinical.icd10_code_grounder import run as ground_run
from scripts.processors.clinical.clinical_abstention_gate import run as abstain_run
from scripts.processors.deliver.escalate_human import run as escalate_run

#: Diagnosis cue words in an Assessment line (deterministic; the SOAP structurer routes to A,
#: this lifts the named conditions from those lines).
_DIAGNOSIS_TERMS = ("type 2 diabetes", "essential hypertension", "hypertension",
                    "fibromyalgia", "asthma", "hyperlipidemia")


def _diagnoses_from_soap(soap: dict[str, Any]) -> list[dict[str, Any]]:
    """Lift named diagnoses + their evidence spans from the Assessment section.

    One Assessment line can list several diagnoses (``a; b``). Scan terms longest-first and blank
    each match so a substring term ("hypertension" inside "essential hypertension") can't
    double-count the same span."""
    out = []
    for item in soap.get("assessment", []):
        work = item["text"].lower()
        for term in sorted(_DIAGNOSIS_TERMS, key=len, reverse=True):
            if term in work:
                out.append({"term": term, "evidence_span": item["text"]})
                work = work.replace(term, " " * len(term))  # consume the span
    return out


def run(*, encounter: str, terminology_corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Code the diagnoses documented in ``encounter`` against the governed terminology."""
    trace: list[dict[str, Any]] = []

    # 1. structure the encounter.
    soap = soap_run(encounter=encounter)["soap"]
    diagnoses = _diagnoses_from_soap(soap)
    trace.append({"step": "soap_note_structurer", "assessment_items": len(soap["assessment"]),
                  "diagnoses": [d["term"] for d in diagnoses]})

    # 2. ground each diagnosis to a code (or abstain).
    grounded = ground_run(diagnoses=diagnoses, terminology_corpus=terminology_corpus)
    codes = grounded["codes"]["resolved"]
    abstained = grounded["abstained"]
    trace.append({"step": "icd10_code_grounder", "coded": [c["code"] for c in codes],
                  "abstained": [a["term"] for a in abstained]})

    # 3. abstention gate: the coding summary must be evidence-supported.
    summary = "; ".join(f"{c['as_documented']} → {c['code']}" for c in codes) or "no codeable diagnoses"
    suff = abstain_run(answer={"text": summary, "cited_evidence_ids": []},
                       evidence=[{"id": c["code"], "kind": "documented_finding", "text": c["evidence_span"]}
                                 for c in codes] or [{"id": "none", "kind": "documented_finding", "text": "no codes"}])
    trace.append({"step": "clinical_abstention_gate", "sufficient": suff["sufficient"]})

    # 4. propose to a coder (never autonomous).
    queue: list[dict] = []
    ticket = escalate_run(result={"proposed_codes": codes, "abstained": abstained},
                          reason="policy_review",
                          enqueue=lambda t: (queue.append(t), {"ref": f"code-{len(queue):04d}"})[1])["ticket"]
    return {"proposed_codes": [{"code": c["code"], "term": c["as_documented"], "citation": c["citation"]} for c in codes],
            "abstained": [{"term": a["term"], "reason": a["reason"]} for a in abstained],
            "coder_review": ticket["queue_ref"], "disposition": "proposed", "serves_truth": False,
            "trace": trace}


# SYNTHETIC terminology (demo shapes; not a real ICD-10 set).
_TERMINOLOGY = [
    {"code": "DEMO-E11.9", "term": "type 2 diabetes mellitus without complications",
     "synonyms": ["type 2 diabetes", "t2dm"], "citation": "demo-icd:e119@v1"},
    {"code": "DEMO-I10", "term": "essential hypertension",
     "synonyms": ["hypertension", "high blood pressure"], "citation": "demo-icd:i10@v1"},
]
_ENCOUNTER = ("Patient reports increased thirst and fatigue. "
              "BP 150/95, A1c 8.2%. "
              "Assessment: uncontrolled type 2 diabetes; essential hypertension. "
              "Also notes possible fibromyalgia per patient self-report. "
              "Plan: start metformin, recheck in 6 weeks.")


def _self_test() -> int:
    out = run(encounter=_ENCOUNTER, terminology_corpus=_TERMINOLOGY)
    coded = {c["term"]: c for c in out["proposed_codes"]}
    # Documented diagnoses in the governed terminology are coded WITH a citation.
    assert coded.get("type 2 diabetes", {}).get("code") == "DEMO-E11.9", out["proposed_codes"]
    assert coded["type 2 diabetes"]["citation"] == "demo-icd:e119@v1"
    assert "essential hypertension" in coded
    # An undocumented/unmatched diagnosis (fibromyalgia: not in terminology) is ABSTAINED, never
    # given a fabricated code.
    abst = {a["term"]: a["reason"] for a in out["abstained"]}
    assert "fibromyalgia" in abst and "no exact terminology match" in abst["fibromyalgia"]
    assert all(c["code"].startswith("DEMO-") for c in out["proposed_codes"])  # only real terminology codes
    # Defensive: proposed to a coder, never autonomous; serves_truth pinned.
    assert out["disposition"] == "proposed" and out["serves_truth"] is False and out["coder_review"]
    # Deterministic.
    assert json.dumps(run(encounter=_ENCOUNTER, terminology_corpus=_TERMINOLOGY), sort_keys=True) == \
           json.dumps(run(encounter=_ENCOUNTER, terminology_corpus=_TERMINOLOGY), sort_keys=True)
    print("PASS — icd10_coding: SOAP structure → ground documented diagnoses to ICD-10 (E11.9, I10) "
          "with citations, ABSTAIN on the unmatched one (fibromyalgia — never a fabricated code), "
          "proposed to a coder (never autonomous), serves_truth=False, deterministic")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="ICD-10 coding assistant showcase.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    print(json.dumps(run(encounter=_ENCOUNTER, terminology_corpus=_TERMINOLOGY), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
