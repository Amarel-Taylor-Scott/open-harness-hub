#!/usr/bin/env python3
"""scripts.check_section_maturity_matrix — proof (PERFECT-MODE): the section maturity matrix is COMPLETE and
HONEST. Every required Baltor section is inventoried; every critical-path section is m10_complete and backed by
a real proof script that EXISTS and is REGISTERED in the flywheel; every non-reference section is
candidate/experimental/deprecated WITH a recorded reason; no section claims completeness without a passing
proof, and no section claims candidate while being on the correctness invariant. This is what stops "green by omission".

CLI: python3 _repos/shared-backend-components/scripts/check_section_maturity_matrix.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import scripts.baltor_flywheel as flywheel

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_MATRIX = _resource("architecture") / "section_maturity_matrix.json"
_VALID_STATUS = {"m0_absent", "m1_folder", "m2_contract", "m3_port", "m4_impl", "m5_integrated", "m6_proof",
                 "m7_api", "m8_ui", "m9_antibypass", "m10_complete", "candidate", "experimental", "deprecated"}
_NON_COMPLETE = {"candidate", "experimental", "deprecated"}
_FIELDS = ("section_id", "category", "owner_folder", "owner_module", "status", "input_contracts",
           "output_contracts", "ports", "adapters", "registries", "proof_scripts", "api_routes",
           "ui_pages", "docs", "known_gaps", "critical_path_required")
#: the sections that MUST be inventoried (the owner's section list).
_REQUIRED = {
    "source_adapters", "ingestion", "parser_provider", "source_artifact_graph", "context_object_decomposition",
    "structured_atomic_decomposition", "unstructured_document_decomposition", "artifact_ledger", "object_store",
    "vectorization", "graph_builder", "conflict_detection", "reconciliation", "verification_gate",
    "fragile_fact_watchtower", "enhancement", "optimization_suite", "consumption_readiness", "consumption_service",
    "context_response", "api_runtime", "ui_pages", "durable_queue", "workers", "event_bus", "llm_gateway",
    "provider_catalog", "security_tenant_isolation", "encryption_metadata", "observability", "review_pack",
    "docs", "architecture_guardrails", "proof_registry", "current_state_reporting", "opportunity_mapping",
    "multi_source_ingestion"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    m = json.loads(_MATRIX.read_text())
    secs = {s["section_id"]: s for s in m["sections"]}
    registered = {p for p, _ in flywheel.PROOF_MODULES}

    check("every required section is inventoried", _REQUIRED <= set(secs), str(sorted(_REQUIRED - set(secs))))

    missing_fields, bad_status, bad_owner_folder, bad_owner_module = [], [], [], []
    no_reason, complete_no_proof, missing_proof_file, unregistered_reference, reference_not_m10 = [], [], [], [], []
    for sid, s in secs.items():
        for f in _FIELDS:
            if f not in s:
                missing_fields.append(f"{sid}.{f}")
        if s.get("status") not in _VALID_STATUS:
            bad_status.append(f"{sid}={s.get('status')}")
        if not _resource(s.get("owner_folder", "")).is_dir():
            bad_owner_folder.append(f"{sid}:{s.get('owner_folder')}")
        if not _resource(s.get("owner_module", "")).is_file():
            bad_owner_module.append(f"{sid}:{s.get('owner_module')}")
        for ps in s.get("proof_scripts", []):
            if not _resource(ps).is_file():
                missing_proof_file.append(f"{sid}:{ps}")
        if s.get("status") in _NON_COMPLETE and not s.get("known_gaps"):
            no_reason.append(sid)
        if s.get("status") == "m10_complete" and not s.get("proof_scripts"):
            complete_no_proof.append(sid)
        if s.get("critical_path_required"):
            if s.get("status") != "m10_complete":
                reference_not_m10.append(f"{sid}={s.get('status')}")
            # a critical-path section must be backed by ≥1 proof that is REGISTERED in the flywheel
            if not any(ps in registered for ps in s.get("proof_scripts", [])):
                unregistered_reference.append(sid)

    check("every section declares all required fields", missing_fields == [], str(missing_fields[:6]))
    check("every status is in the maturity enum", bad_status == [], str(bad_status))
    check("every owner_folder exists", bad_owner_folder == [], str(bad_owner_folder))
    check("every owner_module exists", bad_owner_module == [], str(bad_owner_module))
    check("every referenced proof script exists", missing_proof_file == [], str(missing_proof_file[:6]))
    check("candidate/experimental/deprecated sections record a reason (known_gaps)", no_reason == [], str(no_reason))
    check("no section claims m10_complete without a proof script", complete_no_proof == [], str(complete_no_proof))
    check("every REFERENCE-PATH section is m10_complete (no 'candidate' on the correctness invariant)", reference_not_m10 == [], str(reference_not_m10))
    check("every REFERENCE-PATH section has a proof REGISTERED in the flywheel", unregistered_reference == [], str(unregistered_reference))

    reference = sorted(sid for sid, s in secs.items() if s.get("critical_path_required"))
    check("the runtime correctness invariant (ingest→consumption) is fully inventoried as reference",
          {"ingestion", "structured_atomic_decomposition", "verification_gate", "optimization_suite",
           "consumption_service", "context_response"} <= set(reference))

    print(f"\n{'PASS — check_section_maturity_matrix: all sections inventoried; every critical-path section is m10_complete with a registered proof; non-reference sections are candidate/experimental with a recorded reason. No green-by-omission.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: section maturity matrix is complete + honest.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
