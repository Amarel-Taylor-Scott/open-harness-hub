#!/usr/bin/env python3
"""Primitive registry promotion gate.

Candidate primitive records are useful for search and graph planning, but they are not trusted rows. This gate
blocks promotion unless the record has real provenance, explicit contracts, proof receipts, license/provenance
metadata, graph edges, logs schema, and owner/human approval where required.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


py_const_scripts_check_primitive_registry_promotion_gate__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(py_const_scripts_check_primitive_registry_promotion_gate__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_scripts_check_primitive_registry_promotion_gate__REPO))

from scripts import primitive_registry_builder


py_const_scripts_check_primitive_registry_promotion_gate__BLOCKED = "blocked"
py_const_scripts_check_primitive_registry_promotion_gate__PROMOTION_READY = "promotion_ready"
py_const_scripts_check_primitive_registry_promotion_gate__UNKNOWN_MARKERS = {"unknown", "unknown_candidate", "repo_default_or_unknown", "", None}


def py_function_scripts_check_primitive_registry_promotion_gate__contract_has_unknown(py_arg_scripts_check_primitive_registry_promotion_gate__contract_has_unknown__value):
    if isinstance(py_arg_scripts_check_primitive_registry_promotion_gate__contract_has_unknown__value, dict):
        for py_local_scripts_check_primitive_registry_promotion_gate__contract_has_unknown__item in py_arg_scripts_check_primitive_registry_promotion_gate__contract_has_unknown__value.values():
            if py_function_scripts_check_primitive_registry_promotion_gate__contract_has_unknown(py_local_scripts_check_primitive_registry_promotion_gate__contract_has_unknown__item):
                return True
        return False
    if isinstance(py_arg_scripts_check_primitive_registry_promotion_gate__contract_has_unknown__value, list):
        return any(py_function_scripts_check_primitive_registry_promotion_gate__contract_has_unknown(py_local_scripts_check_primitive_registry_promotion_gate__contract_has_unknown__item) for py_local_scripts_check_primitive_registry_promotion_gate__contract_has_unknown__item in py_arg_scripts_check_primitive_registry_promotion_gate__contract_has_unknown__value)
    if isinstance(py_arg_scripts_check_primitive_registry_promotion_gate__contract_has_unknown__value, str):
        return py_arg_scripts_check_primitive_registry_promotion_gate__contract_has_unknown__value.strip().lower() in py_const_scripts_check_primitive_registry_promotion_gate__UNKNOWN_MARKERS or "unknown_candidate" in py_arg_scripts_check_primitive_registry_promotion_gate__contract_has_unknown__value.lower()
    return False


def py_function_scripts_check_primitive_registry_promotion_gate__proof_receipts_pass(py_arg_scripts_check_primitive_registry_promotion_gate__proof_receipts_pass__record):
    py_local_scripts_check_primitive_registry_promotion_gate__proof_receipts_pass__receipts = py_arg_scripts_check_primitive_registry_promotion_gate__proof_receipts_pass__record.get("proof_receipts") or []
    if not isinstance(py_local_scripts_check_primitive_registry_promotion_gate__proof_receipts_pass__receipts, list) or not py_local_scripts_check_primitive_registry_promotion_gate__proof_receipts_pass__receipts:
        return False
    py_local_scripts_check_primitive_registry_promotion_gate__proof_receipts_pass__command = py_arg_scripts_check_primitive_registry_promotion_gate__proof_receipts_pass__record.get("proof_command")
    return any(receipt.get("status") == "passed" and receipt.get("command") == py_local_scripts_check_primitive_registry_promotion_gate__proof_receipts_pass__command for receipt in py_local_scripts_check_primitive_registry_promotion_gate__proof_receipts_pass__receipts if isinstance(receipt, dict))


def py_function_scripts_check_primitive_registry_promotion_gate__owner_review_pass(py_arg_scripts_check_primitive_registry_promotion_gate__owner_review_pass__record):
    py_local_scripts_check_primitive_registry_promotion_gate__owner_review_pass__review = py_arg_scripts_check_primitive_registry_promotion_gate__owner_review_pass__record.get("promotion_review") or {}
    return isinstance(py_local_scripts_check_primitive_registry_promotion_gate__owner_review_pass__review, dict) and py_local_scripts_check_primitive_registry_promotion_gate__owner_review_pass__review.get("approved") is True and bool(py_local_scripts_check_primitive_registry_promotion_gate__owner_review_pass__review.get("reviewer")) and bool(py_local_scripts_check_primitive_registry_promotion_gate__owner_review_pass__review.get("decision_record"))


def py_function_scripts_check_primitive_registry_promotion_gate__evaluate_record(py_arg_scripts_check_primitive_registry_promotion_gate__evaluate_record__record):
    py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__reasons = []
    py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__candidate_ok, py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__candidate_reason = primitive_registry_builder.py_function_scripts_primitive_registry_builder__validate_candidate_record(py_arg_scripts_check_primitive_registry_promotion_gate__evaluate_record__record)
    if not py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__candidate_ok:
        py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__reasons.append(py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__candidate_reason)
    if py_arg_scripts_check_primitive_registry_promotion_gate__evaluate_record__record.get("serves_truth") is not False:
        py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__reasons.append("serves_truth_forbidden")
    if py_arg_scripts_check_primitive_registry_promotion_gate__evaluate_record__record.get("synthetic"):
        py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__reasons.append("synthetic_records_not_promotable")
    if py_arg_scripts_check_primitive_registry_promotion_gate__evaluate_record__record.get("llm_generated"):
        py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__reasons.append("llm_generated_candidate_not_truth")
    if py_function_scripts_check_primitive_registry_promotion_gate__contract_has_unknown(py_arg_scripts_check_primitive_registry_promotion_gate__evaluate_record__record.get("input_contract")) or py_function_scripts_check_primitive_registry_promotion_gate__contract_has_unknown(py_arg_scripts_check_primitive_registry_promotion_gate__evaluate_record__record.get("output_contract")):
        py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__reasons.append("unresolved_contract")
    py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__license_provenance = py_arg_scripts_check_primitive_registry_promotion_gate__evaluate_record__record.get("license_provenance") or {}
    if not isinstance(py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__license_provenance, dict) or str(py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__license_provenance.get("license", "")).lower() in py_const_scripts_check_primitive_registry_promotion_gate__UNKNOWN_MARKERS:
        py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__reasons.append("license_not_resolved")
    if not py_function_scripts_check_primitive_registry_promotion_gate__proof_receipts_pass(py_arg_scripts_check_primitive_registry_promotion_gate__evaluate_record__record):
        py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__reasons.append("missing_passing_proof_receipt")
    if not py_function_scripts_check_primitive_registry_promotion_gate__owner_review_pass(py_arg_scripts_check_primitive_registry_promotion_gate__evaluate_record__record):
        py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__reasons.append("missing_owner_review")
    py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__decision = py_const_scripts_check_primitive_registry_promotion_gate__BLOCKED if py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__reasons else py_const_scripts_check_primitive_registry_promotion_gate__PROMOTION_READY
    return {
        "record_id": py_arg_scripts_check_primitive_registry_promotion_gate__evaluate_record__record.get("id"),
        "decision": py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__decision,
        "reasons": sorted(set(py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__reasons)),
        "serves_truth": False,
        "promotion_allowed": py_local_scripts_check_primitive_registry_promotion_gate__evaluate_record__decision == py_const_scripts_check_primitive_registry_promotion_gate__PROMOTION_READY,
    }


def py_function_scripts_check_primitive_registry_promotion_gate__promoted_record(py_arg_scripts_check_primitive_registry_promotion_gate__promoted_record__record, py_arg_scripts_check_primitive_registry_promotion_gate__promoted_record__decision):
    if py_arg_scripts_check_primitive_registry_promotion_gate__promoted_record__decision.get("decision") != py_const_scripts_check_primitive_registry_promotion_gate__PROMOTION_READY:
        raise ValueError("cannot promote blocked primitive record")
    return {
        **py_arg_scripts_check_primitive_registry_promotion_gate__promoted_record__record,
        "candidate": False,
        "promotion_status": py_const_scripts_check_primitive_registry_promotion_gate__PROMOTION_READY,
        "promotion_decision": py_arg_scripts_check_primitive_registry_promotion_gate__promoted_record__decision,
        "serves_truth": False,
    }


def py_function_scripts_check_primitive_registry_promotion_gate__make_ready_record(py_arg_scripts_check_primitive_registry_promotion_gate__make_ready_record__base):
    py_local_scripts_check_primitive_registry_promotion_gate__make_ready_record__ready = dict(py_arg_scripts_check_primitive_registry_promotion_gate__make_ready_record__base)
    py_local_scripts_check_primitive_registry_promotion_gate__make_ready_record__ready["input_contract"] = {"shape": "object", "fields": {"rate_text": "string"}}
    py_local_scripts_check_primitive_registry_promotion_gate__make_ready_record__ready["output_contract"] = {"shape": "object", "fields": {"rate": "number", "jurisdiction": "string"}}
    py_local_scripts_check_primitive_registry_promotion_gate__make_ready_record__ready["license_provenance"] = {
        **py_local_scripts_check_primitive_registry_promotion_gate__make_ready_record__ready["license_provenance"],
        "license": "MIT",
        "reviewed": True,
    }
    py_local_scripts_check_primitive_registry_promotion_gate__make_ready_record__ready["proof_receipts"] = [
        {
            "command": py_local_scripts_check_primitive_registry_promotion_gate__make_ready_record__ready["proof_command"],
            "status": "passed",
            "run_id": "proof-fixture-001",
            "serves_truth": False,
        }
    ]
    py_local_scripts_check_primitive_registry_promotion_gate__make_ready_record__ready["promotion_review"] = {
        "approved": True,
        "reviewer": "owner",
        "decision_record": "promotion-fixture-001",
        "serves_truth": False,
    }
    return py_local_scripts_check_primitive_registry_promotion_gate__make_ready_record__ready


def py_function_scripts_check_primitive_registry_promotion_gate__self_test():
    py_local_scripts_check_primitive_registry_promotion_gate__self_test__failures = []

    def py_function_scripts_check_primitive_registry_promotion_gate__self_test__check(py_arg_scripts_check_primitive_registry_promotion_gate__self_test_check__name, py_arg_scripts_check_primitive_registry_promotion_gate__self_test_check__ok, py_arg_scripts_check_primitive_registry_promotion_gate__self_test_check__detail=""):
        print(f"  [{'ok' if py_arg_scripts_check_primitive_registry_promotion_gate__self_test_check__ok else 'FAIL'}] {py_arg_scripts_check_primitive_registry_promotion_gate__self_test_check__name}{(': ' + py_arg_scripts_check_primitive_registry_promotion_gate__self_test_check__detail) if py_arg_scripts_check_primitive_registry_promotion_gate__self_test_check__detail and not py_arg_scripts_check_primitive_registry_promotion_gate__self_test_check__ok else ''}")
        if not py_arg_scripts_check_primitive_registry_promotion_gate__self_test_check__ok:
            py_local_scripts_check_primitive_registry_promotion_gate__self_test__failures.append(py_arg_scripts_check_primitive_registry_promotion_gate__self_test_check__name)

    with tempfile.TemporaryDirectory() as py_local_scripts_check_primitive_registry_promotion_gate__self_test__tmp:
        py_inst_scripts_check_primitive_registry_promotion_gate__self_test__root = Path(py_local_scripts_check_primitive_registry_promotion_gate__self_test__tmp)
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__inventory = primitive_registry_builder.py_function_scripts_primitive_registry_builder__write_fixture_inventory(py_inst_scripts_check_primitive_registry_promotion_gate__self_test__root)
        py_local_scripts_check_primitive_registry_promotion_gate__self_test___, py_local_scripts_check_primitive_registry_promotion_gate__self_test__records, py_local_scripts_check_primitive_registry_promotion_gate__self_test___, py_local_scripts_check_primitive_registry_promotion_gate__self_test___ = primitive_registry_builder.py_function_scripts_primitive_registry_builder__build(py_local_scripts_check_primitive_registry_promotion_gate__self_test__inventory, py_inst_scripts_check_primitive_registry_promotion_gate__self_test__root / "out", 100, True)
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__base = py_local_scripts_check_primitive_registry_promotion_gate__self_test__records[0]
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__base_decision = py_function_scripts_check_primitive_registry_promotion_gate__evaluate_record(py_local_scripts_check_primitive_registry_promotion_gate__self_test__base)
        py_function_scripts_check_primitive_registry_promotion_gate__self_test__check("builder candidate is valid but blocked from promotion until contracts/proofs/review resolve", py_local_scripts_check_primitive_registry_promotion_gate__self_test__base_decision["decision"] == py_const_scripts_check_primitive_registry_promotion_gate__BLOCKED and {"unresolved_contract", "license_not_resolved", "missing_passing_proof_receipt", "missing_owner_review"} <= set(py_local_scripts_check_primitive_registry_promotion_gate__self_test__base_decision["reasons"]), json.dumps(py_local_scripts_check_primitive_registry_promotion_gate__self_test__base_decision, sort_keys=True))

        py_local_scripts_check_primitive_registry_promotion_gate__self_test__placeholder = dict(py_local_scripts_check_primitive_registry_promotion_gate__self_test__base)
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__placeholder["purpose"] = "TODO placeholder text"
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__placeholder_decision = py_function_scripts_check_primitive_registry_promotion_gate__evaluate_record(py_local_scripts_check_primitive_registry_promotion_gate__self_test__placeholder)
        py_function_scripts_check_primitive_registry_promotion_gate__self_test__check("placeholder records are blocked", py_local_scripts_check_primitive_registry_promotion_gate__self_test__placeholder_decision["decision"] == py_const_scripts_check_primitive_registry_promotion_gate__BLOCKED and "placeholder_text" in py_local_scripts_check_primitive_registry_promotion_gate__self_test__placeholder_decision["reasons"])

        py_local_scripts_check_primitive_registry_promotion_gate__self_test__synthetic = dict(py_local_scripts_check_primitive_registry_promotion_gate__self_test__base)
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__synthetic["synthetic"] = True
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__synthetic["example_record"] = True
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__synthetic_decision = py_function_scripts_check_primitive_registry_promotion_gate__evaluate_record(py_local_scripts_check_primitive_registry_promotion_gate__self_test__synthetic)
        py_function_scripts_check_primitive_registry_promotion_gate__self_test__check("synthetic/example rows are not promotable", py_local_scripts_check_primitive_registry_promotion_gate__self_test__synthetic_decision["decision"] == py_const_scripts_check_primitive_registry_promotion_gate__BLOCKED and "synthetic_records_not_promotable" in py_local_scripts_check_primitive_registry_promotion_gate__self_test__synthetic_decision["reasons"])

        py_local_scripts_check_primitive_registry_promotion_gate__self_test__llm_generated = py_function_scripts_check_primitive_registry_promotion_gate__make_ready_record(py_local_scripts_check_primitive_registry_promotion_gate__self_test__base)
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__llm_generated["llm_generated"] = True
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__llm_decision = py_function_scripts_check_primitive_registry_promotion_gate__evaluate_record(py_local_scripts_check_primitive_registry_promotion_gate__self_test__llm_generated)
        py_function_scripts_check_primitive_registry_promotion_gate__self_test__check("LLM-generated candidates are blocked as truth", py_local_scripts_check_primitive_registry_promotion_gate__self_test__llm_decision["decision"] == py_const_scripts_check_primitive_registry_promotion_gate__BLOCKED and "llm_generated_candidate_not_truth" in py_local_scripts_check_primitive_registry_promotion_gate__self_test__llm_decision["reasons"])

        py_local_scripts_check_primitive_registry_promotion_gate__self_test__truthy = py_function_scripts_check_primitive_registry_promotion_gate__make_ready_record(py_local_scripts_check_primitive_registry_promotion_gate__self_test__base)
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__truthy["serves_truth"] = True
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__truthy_decision = py_function_scripts_check_primitive_registry_promotion_gate__evaluate_record(py_local_scripts_check_primitive_registry_promotion_gate__self_test__truthy)
        py_function_scripts_check_primitive_registry_promotion_gate__self_test__check("records cannot request serves_truth=true", py_local_scripts_check_primitive_registry_promotion_gate__self_test__truthy_decision["decision"] == py_const_scripts_check_primitive_registry_promotion_gate__BLOCKED and ("serves_truth_forbidden" in py_local_scripts_check_primitive_registry_promotion_gate__self_test__truthy_decision["reasons"] or "serves_truth_must_be_false" in py_local_scripts_check_primitive_registry_promotion_gate__self_test__truthy_decision["reasons"]))

        py_local_scripts_check_primitive_registry_promotion_gate__self_test__ready = py_function_scripts_check_primitive_registry_promotion_gate__make_ready_record(py_local_scripts_check_primitive_registry_promotion_gate__self_test__base)
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__ready_decision = py_function_scripts_check_primitive_registry_promotion_gate__evaluate_record(py_local_scripts_check_primitive_registry_promotion_gate__self_test__ready)
        py_function_scripts_check_primitive_registry_promotion_gate__self_test__check("reviewed/proven/resolved real-code record becomes promotion-ready", py_local_scripts_check_primitive_registry_promotion_gate__self_test__ready_decision["decision"] == py_const_scripts_check_primitive_registry_promotion_gate__PROMOTION_READY and py_local_scripts_check_primitive_registry_promotion_gate__self_test__ready_decision["promotion_allowed"] is True, json.dumps(py_local_scripts_check_primitive_registry_promotion_gate__self_test__ready_decision, sort_keys=True))
        py_local_scripts_check_primitive_registry_promotion_gate__self_test__promoted = py_function_scripts_check_primitive_registry_promotion_gate__promoted_record(py_local_scripts_check_primitive_registry_promotion_gate__self_test__ready, py_local_scripts_check_primitive_registry_promotion_gate__self_test__ready_decision)
        py_function_scripts_check_primitive_registry_promotion_gate__self_test__check("promotion projection still never serves truth", py_local_scripts_check_primitive_registry_promotion_gate__self_test__promoted["candidate"] is False and py_local_scripts_check_primitive_registry_promotion_gate__self_test__promoted["serves_truth"] is False and py_local_scripts_check_primitive_registry_promotion_gate__self_test__promoted["promotion_decision"]["serves_truth"] is False)

    if py_local_scripts_check_primitive_registry_promotion_gate__self_test__failures:
        print(f"\nFAIL - check_primitive_registry_promotion_gate: {len(py_local_scripts_check_primitive_registry_promotion_gate__self_test__failures)} failure(s)")
        return 1
    print("\nPASS - check_primitive_registry_promotion_gate: primitive promotion gate blocks unsafe rows and accepts only proven reviewed records")
    return 0


def main():
    return py_function_scripts_check_primitive_registry_promotion_gate__self_test()


if __name__ == "__main__":
    raise SystemExit(main())
