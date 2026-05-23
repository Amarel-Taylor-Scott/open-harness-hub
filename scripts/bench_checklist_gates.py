#!/usr/bin/env python3
"""Auto-benchmark all checklist-gate pipelines: clean = GO, flagged = NOGO."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_pipeline import run_pipeline, load_catalog


CHECKLIST_BENCHES = [
    # (label, pipeline_id, expected_clean_input, expected_flagged_input, input_key)
    ("WHO Surgical Safety",   "pipeline/who-surgical-safety-gate",
     "data/checklist-samples/who-ssc-clean.json",
     "data/checklist-samples/who-ssc-flagged.json", "preinduction_packet"),
    ("FAA Before-Takeoff",    "pipeline/faa-preflight-gate",
     "data/checklist-samples/faa-before-takeoff-clean.json",
     "data/checklist-samples/faa-before-takeoff-flagged.json", "preflight_packet"),
    ("MSHA Pre-Shift Exam",   "pipeline/msha-preshift-exam",
     "data/checklist-samples/msha-preshift-clean.json",
     "data/checklist-samples/msha-preshift-flagged.json", "preshift_packet"),
    ("PSM PSSR",              "pipeline/pssr-startup-gate",
     "data/checklist-samples/pssr-clean.json",
     "data/checklist-samples/pssr-flagged.json", "pssr_packet"),
    ("AORN Surgical Count",   "pipeline/aorn-surgical-count-gate",
     "data/checklist-samples/aorn-count-clean.json",
     "data/checklist-samples/aorn-count-flagged.json", "or_packet"),
    ("ITIL Change Enablement","pipeline/itil-change-gate",
     "data/checklist-samples/itil-change-clean.json",
     "data/checklist-samples/itil-change-flagged.json", "change_packet"),
    ("KYC/CIP Onboarding",    "pipeline/kyc-cip-gate",
     "data/checklist-samples/kyc-cip-clean.json",
     "data/checklist-samples/kyc-cip-flagged.json", "onboarding_packet"),
    ("TRID Loan Disclosure",  "pipeline/trid-loan-gate",
     "data/checklist-samples/trid-loan-clean.json",
     "data/checklist-samples/trid-loan-flagged.json", "loan_packet"),
    ("ESI ED Triage",          "pipeline/esi-triage-gate",
     "data/checklist-samples/esi-triage-clean.json",
     "data/checklist-samples/esi-triage-flagged.json", "triage_packet"),
    ("HACCP CCP",              "pipeline/haccp-ccp-gate",
     "data/checklist-samples/haccp-ccp-clean.json",
     "data/checklist-samples/haccp-ccp-flagged.json", "ccp_packet"),
    ("NIST 800-61 IR",         "pipeline/nist-800-61-ir-gate",
     "data/checklist-samples/nist-800-61-clean.json",
     "data/checklist-samples/nist-800-61-flagged.json", "incident_packet"),
    ("DOT Pre-Trip DVIR",      "pipeline/dot-pretrip-gate",
     "data/checklist-samples/dot-pretrip-clean.json",
     "data/checklist-samples/dot-pretrip-flagged.json", "dvir_packet"),
    ("NFPA 70E LOTO",          "pipeline/nfpa-70e-loto-gate",
     "data/checklist-samples/nfpa70e-loto-clean.json",
     "data/checklist-samples/nfpa70e-loto-flagged.json", "loto_packet"),
]


def gate_verdict(result: dict) -> str:
    for step in result["trace"]:
        if step.get("ref") == "processor/checklist-evaluator":
            return step["output"]["verdict"]
    return "missing-gate"


def main() -> int:
    catalog = load_catalog()
    failures = []
    print(f"{'Checklist gate':30s}  {'clean':10s}  {'flagged':10s}")
    print("-" * 55)
    for label, pid, clean_p, flagged_p, key in CHECKLIST_BENCHES:
        if pid not in catalog:
            failures.append((label, "pipeline missing"))
            continue
        pipeline = catalog[pid]
        clean_v = gate_verdict(run_pipeline(pipeline, {key: json.loads(Path(clean_p).read_text())}, simulate=False))
        flag_v = gate_verdict(run_pipeline(pipeline, {key: json.loads(Path(flagged_p).read_text())}, simulate=False))
        clean_ok = clean_v == "go"
        flag_ok = flag_v == "nogo"
        if not clean_ok:
            failures.append((label, f"clean sample returned {clean_v}, expected go"))
        if not flag_ok:
            failures.append((label, f"flagged sample returned {flag_v}, expected nogo"))
        print(f"{label:30s}  {clean_v:10s}  {flag_v:10s}  {'OK' if (clean_ok and flag_ok) else 'FAIL'}")
    print()
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for l, r in failures:
            print(f"  {l}: {r}")
        return 1
    print(f"All {len(CHECKLIST_BENCHES)} checklist gates pass clean=GO + flagged=NOGO.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
