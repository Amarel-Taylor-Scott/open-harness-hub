#!/usr/bin/env python3
"""Seed highly-specific clinical decision-SUPPORT components (the deterministic gates the
/compare demo references). DEFENSIVE / decision-support only — every one routes to a clinician,
grounds on a corpus, or abstains; none gives autonomous medical advice. Synthetic/spec; no PII.

Same iteration pattern as scripts/seed_retrieval_taxonomy_components.py — extend COMPONENTS to add
more. Run: python3 scripts/seed_clinical_triage_components.py && python3 scripts/validate.py catalog/processors/clinical/*.yaml
"""
from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "catalog" / "processors" / "clinical"
DATE = "2026-05-29"

# slug, name, process_kind, capability, deterministic, side_effects, inputs, outputs, why
COMPONENTS = [
    ("clinical-redflag-screen", "Clinical red-flag screen", "gate.clinical_redflag",
     ["safety_gating", "classification"], True, "none", ["note", "vitals"], ["red_flags", "escalate"],
     "Deterministic pattern screen over a clinical note + vitals for time-critical RED-FLAG syndromes "
     "(ACS: chest pain + radiation + diaphoresis; sepsis: qSOFA; stroke: FAST; PE). On a fired flag it "
     "ESCALATES to a clinician and forbids reassurance — decision-support, not a diagnosis. The bare "
     "model's most dangerous failure is missing these; this gate catches them with no model call."),
    ("drug-interaction-checker", "Drug-interaction checker", "verify.drug_interaction",
     ["verification"], True, "read", ["med_list", "interaction_corpus"], ["interactions", "severity"],
     "Deterministic lookup of every drug pair in a medication list against a governed interaction "
     "corpus (e.g. warfarin × azole-antifungals → CYP2C9 → major). Returns severity-tiered hits with "
     "the corpus citation + a prescriber-flag action — never a model guess about safety."),
    ("icd10-code-grounder", "ICD-10 code grounder", "coerce.icd_ground",
     ["extraction", "verification"], True, "read", ["diagnoses", "terminology_corpus"], ["codes", "abstained"],
     "Resolve each candidate diagnosis to an ICD-10-CM code via exact-id lookup against a terminology "
     "corpus and link it to the documented evidence span. Undocumented diagnoses are left UNCODED "
     "(abstain) — eliminates the bare model's habit of fabricating plausible-but-wrong codes."),
    ("soap-note-structurer", "SOAP-note structurer", "format_convert.soap_note",
     ["extraction", "summarization"], True, "none", ["encounter"], ["soap"],
     "Structure a dictated/free-text encounter into Subjective / Objective / Assessment / Plan sections, "
     "each item linked to its source span. Deterministic structuring; coded diagnoses are deferred to "
     "the ICD grounder so codes are never invented here."),
    ("clinical-abstention-gate", "Clinical abstention gate", "gate.evidence_sufficiency",
     ["safety_gating", "governance"], True, "none", ["answer", "evidence"], ["sufficient", "reason"],
     "Block a clinical answer when the documented/retrieved evidence is insufficient to support it, "
     "routing to 'insufficient evidence — clinician review' instead of guessing. The cite-or-abstain "
     "contract that converts retrieval into safe, governed clinical decision-support."),
    ("lab-critical-value-flag", "Lab critical-value flag", "gate.lab_critical_value",
     ["safety_gating", "classification"], True, "read", ["labs", "reference_ranges"], ["critical", "escalate"],
     "Compare lab results against governed reference + critical-value thresholds (e.g. K+ > 6.5, "
     "glucose < 40) and escalate critical values immediately. Deterministic; no model call; the panic-"
     "value safety net."),
    ("allergy-contraindication-check", "Allergy / contraindication check", "verify.allergy_contraindication",
     ["verification", "safety_gating"], True, "read", ["orders", "allergies", "conditions"], ["conflicts"],
     "Check ordered medications/procedures against the patient's documented allergies and "
     "contraindicated conditions (e.g. NSAID with CKD, penicillin allergy). Deterministic conflict "
     "detection with the documented source — blocks contraindicated orders, routes to review."),
    ("dosage-range-validator", "Dosage-range validator", "verify.dosage_range",
     ["verification"], True, "read", ["order", "patient", "dose_corpus"], ["in_range", "adjusted"],
     "Validate a medication dose against weight-/age-/renal-adjusted ranges from a governed dosing "
     "corpus, flagging out-of-range and suggesting the adjusted range with citation. Deterministic; "
     "decision-support for the prescriber, not an autonomous order."),
]
TAXO_NOTE = ("Clinical decision-SUPPORT component — DEFENSIVE only: grounds on a governed corpus, "
             "fires a deterministic gate, and/or routes to a clinician; never autonomous medical advice. "
             "Lift is measured at the pipeline level.")


def build(c: tuple) -> dict:
    slug, name, pk, cap, det, side, ins, outs, why = c
    return {
        "id": f"processor/{slug}",
        "type": "processor",
        "version": "0.1.0",
        "name": name,
        "description": why + "\n\n" + TAXO_NOTE,
        "authors": [{"name": "OpenHubForAI contributors"}],
        "license": "MIT",
        "industry": ["healthcare"],
        "capability": cap,
        "modality": ["text", "structured"],
        "lifecycle": "experimental",
        "trust_boundary": "local",
        "tags": ["clinical", "decision-support", "deterministic-gate", "freezable" if det else "model-assisted", "governed"],
        "created": DATE,
        "updated": DATE,
        "process_kind": pk,
        "deterministic": det,
        "idempotent": True,
        "streaming": False,
        "inputs": [{"name": n, "type": "object"} for n in ins],
        "outputs": [{"name": n, "type": "object"} for n in outs],
        "side_effects": side,
        "on_error": "raise",
        "implementations": [{"kind": "callable", "path": f"scripts.processors.clinical.{slug.replace('-', '_')}.run", "language": "python"}],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for c in COMPONENTS:
        (OUT / f"{c[0]}.yaml").write_text(yaml.safe_dump(build(c), sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
    print(f"wrote {len(COMPONENTS)} clinical decision-support components to {OUT.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
