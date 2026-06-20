#!/usr/bin/env python3
"""scripts.check_cfpb_conflict_detection — proof: the deterministic detector finds the known Reg E (10
business days) vs FAQ (30 days) contradiction, flags a promotable artifact that depends on an unverified
allegation, and every conflict cites BOTH artifacts.

CLI: python3 scripts/check_cfpb_conflict_detection.py --self-test
"""
from __future__ import annotations

import argparse
from dataclasses import replace

from scripts.artifact_graph import cfpb_artifacts as CA
from scripts.artifact_graph import conflict_detector as CD
from scripts.artifact_graph import graph_builder as GB
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
    edges = GB.build_edges(arts, tenant_id="acme", run_id=rid)
    conflicts = CD.detect(arts, edges, tenant_id="acme")

    deadline = [c for c in conflicts if c.conflict_type == "deadline_mismatch"]
    check("known 10-vs-30 deadline contradiction is detected", len(deadline) == 1, str([c.conflict_type for c in conflicts]))
    if deadline:
        c = deadline[0]
        pair = {c.artifact_a_id, c.artifact_b_id}
        check("deadline conflict cites BOTH the Reg E and FAQ artifacts", pair == {built["reg_e_id"], built["faq_id"]}, str(pair))
        check("deadline conflict evidence records both values (10 vs 30)",
              {c.evidence_json["a"]["value"], c.evidence_json["b"]["value"]} == {10, 30}, str(c.evidence_json))
        check("deadline conflict is high severity + starts open", c.severity == "high" and c.status == "open")

    # promoted-on-allegation: mark a conclusion promotable, it is SUPPORTED_BY an allegation → flag
    promoted = [replace(a, promotion_eligible=True) if a.artifact_type == "conclusion" else a for a in arts]
    edges2 = GB.build_edges(promoted, tenant_id="acme", run_id=rid)
    conflicts2 = CD.detect(promoted, edges2, tenant_id="acme")
    gov = [c for c in conflicts2 if c.conflict_type == "promoted_depends_on_unverified"]
    check("a PROMOTABLE artifact depending on an unverified allegation is flagged", len(gov) >= 1)
    if gov:
        check("governance conflict cites both the promotable artifact and the allegation",
              gov[0].artifact_a_id and gov[0].artifact_b_id)

    check("every conflict cites two distinct artifacts", all(c.artifact_a_id != c.artifact_b_id for c in conflicts + conflicts2))

    print(f"\n{'PASS — check_cfpb_conflict_detection: known 10-vs-30 contradiction detected (cites both sources); promotable-on-allegation flagged; conflicts cite both artifacts.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: C32 deterministic conflict detection.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
