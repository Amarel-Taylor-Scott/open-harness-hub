#!/usr/bin/env python3
"""scripts.check_cfpb_reconciliation — proof: deterministic reconciliation makes Reg E (source-of-law) beat
the FAQ summary, holds out the losing artifact, and emits a reconciliation receipt.

CLI: python3 _repos/shared-backend-components/scripts/check_cfpb_reconciliation.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.artifact_graph import cfpb_artifacts as CA
from scripts.artifact_graph import conflict_detector as CD
from scripts.artifact_graph import graph_builder as GB
from scripts.artifact_graph import reconciliation as RC
from scripts.security.tenant_catalog import TenantPolicy

REC = [{"complaint_id": "CFPB-1", "product": "Credit card", "issue": "Billing dispute", "company": "Acme",
        "state": "CA", "date_received": "2026-01-02",
        "consumer_complaint_narrative": "I was charged twice. The company refused to refund me."}]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    built = CA.build_artifacts(REC, TenantPolicy("acme"))
    arts, rid = built["artifacts"], built["run_id"]
    by_id = {a.artifact_id: a for a in arts}
    edges = GB.build_edges(arts, tenant_id="acme", run_id=rid)
    conflicts = CD.detect(arts, edges, tenant_id="acme")
    rec = RC.reconcile(conflicts, by_id, tenant_id="acme")

    recons = rec["reconciliations"]
    check("a reconciliation was produced for the conflict", len(recons) >= 1)
    authority = [r for r in recons if r.decision == "resolved_by_authority"]
    check("deadline conflict resolved by AUTHORITY (regulation > FAQ)", len(authority) == 1, str([r.decision for r in recons]))
    if authority:
        r = authority[0]
        check("Reg E (10 business days) is the WINNING artifact", r.winning_artifact_id == built["reg_e_id"])
        check("the lower-authority FAQ (30 days) is HELD OUT", built["faq_id"] in rec["held_out_ids"])
        check("reconciliation emits a receipt with decision + winner + held-out + reason + evidence",
              all(k in r.receipt_json for k in ("decision", "winning_artifact_id", "held_out_artifact_ids", "reason", "evidence")))
        check("receipt rationale names the authority precedence", "rank" in r.rationale.lower() or "outrank" in r.rationale.lower(), r.rationale)
        check("resolver_type is deterministic (human-signed is a documented hook only)", r.resolver_type == "deterministic")

    check("the winning Reg E artifact is NOT itself held out", built["reg_e_id"] not in rec["held_out_ids"])

    print(f"\n{'PASS — check_cfpb_reconciliation: source-of-law beats FAQ summary; losing claim held out; reconciliation receipt written.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: C32 deterministic reconciliation + receipt.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
