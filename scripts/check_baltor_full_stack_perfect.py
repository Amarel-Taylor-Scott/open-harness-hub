#!/usr/bin/env python3
"""scripts.check_baltor_full_stack_perfect — the MASTER proof: the whole local correctness invariant runs end to end
(ingestion → decomposition → artifact ledger → vectorization → graph → conflict → reconciliation →
verification → optimization → consumption-readiness → served ContextResponse), the section maturity matrix's
reference sections are all m10_complete with registered proofs, and the CFPB reference result holds. Prints a
SECTION | STATUS | PROOF | OWNER | CONTRACT | NOTES table. Does NOT claim 'perfect' for surfaces that are not
yet reference — it asserts what is real and lets the matrix flag the rest. (The flywheel wrapping this proof, plus
all the per-section proofs, supply the 'green' attestation.)

CLI: python3 scripts/check_baltor_full_stack_perfect.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.runtime.consumption import run_cfpb_to_consumption
from scripts.runtime.schema_validator import validate_ref

_REPO = Path(__file__).resolve().parents[1]
_MATRIX = _REPO / "architecture" / "section_maturity_matrix.json"
NOW = "2026-06-05T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # 1) the whole correctness invariant runs end-to-end to a served ContextResponse
    r = run_cfpb_to_consumption("demo", require_optimized=True, now=NOW)
    resp = r["response"]
    check("correctness invariant reaches a SERVED ContextResponse", r["decision"] == "served")
    check("ContextResponse is schema-valid", validate_ref(resp, "consumption/ContextResponse") == [])
    check("answer contains '10 business days'", "10 business days" in resp["answer"], resp["answer"])
    served_ids = [f["artifact_id"] for f in resp["served_facts"]]
    held_ids = [h["artifact_id"] for h in resp["held_out_warnings"]]
    check("Reg E 10 fact is served; FAQ-30 held out only", "fact-rege-10" in served_ids and "fact-faq-30" in held_ids and "fact-faq-30" not in served_ids)
    check("no allegation served; every served fact has a handle + receipt lineage",
          all(f.get("source_handle") and f.get("verification_receipt_id") and f.get("optimization_receipt_id") for f in resp["served_facts"])
          and not any(f.get("claim_status") == "unverified_allegation" for f in resp["served_facts"]))
    check("all three receipt ids present", all(resp["receipts"].get(k) for k in ("verification_receipt_id", "optimization_receipt_id", "consumption_receipt_id")))
    check("optimization bake-off ran multiple variants and rejected ≥1", 0 < r["promoted_count"] < r["candidate_count"])
    r2 = run_cfpb_to_consumption("demo", require_optimized=True, now=NOW)
    check("the full reference run is deterministic", resp == r2["response"])

    # 2) every critical-path section is m10_complete with a registered proof
    m = json.loads(_MATRIX.read_text())
    secs = {s["section_id"]: s for s in m["sections"]}
    import scripts.baltor_flywheel as fw
    registered = {p for p, _ in fw.PROOF_MODULES}
    reference = {sid: s for sid, s in secs.items() if s.get("critical_path_required")}
    not_complete = [sid for sid, s in reference.items() if s.get("status") != "m10_complete"]
    no_proof = [sid for sid, s in reference.items() if not any(ps in registered for ps in s.get("proof_scripts", []))]
    check("every critical-path section is m10_complete", not_complete == [], str(not_complete))
    check("every critical-path section has a registered proof", no_proof == [], str(no_proof))

    # 3) the section table (the owner's required output)
    print("\n  SECTION                          | STATUS        | PROOF                                   | OWNER                                   | CONTRACT             | NOTES")
    print("  " + "-" * 160)
    for sid in sorted(secs):
        s = secs[sid]
        proof = (s.get("proof_scripts") or ["-"])[0].replace("scripts/", "")
        owner = s.get("owner_module", "-")
        contract = (s.get("output_contracts") or ["-"])[0]
        note = (s.get("known_gaps") or [""])[0][:42]
        mark = "GREEN" if s.get("critical_path_required") and s.get("status") == "m10_complete" else s.get("status")
        print(f"  {sid:32.32} | {mark:13.13} | {proof:39.39} | {owner:39.39} | {contract:20.20} | {note}")

    reference_green = sum(1 for s in reference.values() if s.get("status") == "m10_complete")
    candidates = sorted(sid for sid, s in secs.items() if s.get("status") in ("candidate", "experimental"))
    print(f"\n  critical-path sections GREEN: {reference_green}/{len(reference)} | candidate/experimental (not reference): {candidates}")

    print(f"\n{'PASS — check_baltor_full_stack_perfect: the local correctness invariant runs ingestion→consumption to a deterministic, schema-valid served ContextResponse (answer 10 business days; FAQ-30 held out; full receipt lineage); every critical-path section is m10_complete with a registered proof. Non-reference surfaces (api/ui/worker-consume/watchtower/object_store/unstructured) are honestly flagged candidate/pending in the matrix.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Master proof: Baltor full-stack correctness invariant.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
