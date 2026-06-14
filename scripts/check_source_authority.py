#!/usr/bin/env python3
"""scripts.check_source_authority — PROOF: source authority is EARNED from provenance, not assigned.

The moat claim is "Baltor establishes which source is authoritative." This gate proves the engine
DERIVES authority from a source's publisher/domain (+ verified provenance) via
scripts/artifact_graph/source_authority against architecture/source_authority_registry.json — and that
the CFPB flagship's Reg-E-beats-FAQ outcome is CONTINGENT on that provenance:

  - the classifier ranks the eCFR (source-of-law) above an unlisted vendor blog (unverified);
  - an UNSIGNED claim to a top-tier domain is DOWNGRADED (claimed != verified);
  - in the real reconciliation, Reg-E wins with an authority_basis that NAMES the eCFR provenance;
  - FLIP THE PUBLISHER: republish Reg-E on a vendor blog and it STOPS winning by authority — so the
    win was earned, not a fixture number someone typed.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import sys

from scripts.artifact_graph import cfpb_artifacts as CA
from scripts.artifact_graph import conflict_detector as CD
from scripts.artifact_graph import graph_builder as GB
from scripts.artifact_graph import reconciliation as RC
from scripts.artifact_graph import source_authority as SA
from scripts.security.tenant_catalog import TenantPolicy

_REC = [{"complaint_id": "CFPB-1", "product": "Credit card", "issue": "Billing dispute", "company": "Acme",
         "state": "CA", "date_received": "2026-01-02", "consumer_complaint_narrative": "x"}]


def _authority_winner(rec: dict):
    hits = [r for r in rec["reconciliations"] if r.decision == "resolved_by_authority"]
    return hits[0] if hits else None


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # 1. the classifier derives authority from provenance (re-uses its own self-tested invariants)
    ck("classifier: eCFR → source_of_law (rank 100)",
       SA.classify(source_uri="https://www.ecfr.gov/x")["rank"] == 100)
    ck("classifier: an unlisted vendor blog earns rank 10 (unverified)",
       SA.classify(source_uri="https://acme-compliance.example.com/x")["tier"] == "unverified")
    ck("classifier: unsigned claim to a top-tier domain is DOWNGRADED (claimed != verified)",
       SA.classify(source_uri="https://treasury.gov/x", signed=False)["downgraded"] is True)

    # 2. in the REAL reconciliation, Reg-E wins and the authority_basis NAMES the eCFR provenance (earned)
    built = CA.build_artifacts(_REC, TenantPolicy("acme"))
    by_id = {a.artifact_id: a for a in built["artifacts"]}
    edges = GB.build_edges(built["artifacts"], tenant_id="acme", run_id=built["run_id"])
    conflicts = CD.detect(built["artifacts"], edges, tenant_id="acme")
    rec = RC.reconcile(conflicts, by_id, tenant_id="acme")
    win = _authority_winner(rec)
    ck("Reg-E wins the deadline conflict by AUTHORITY", win is not None and win.winning_artifact_id == built["reg_e_id"])
    if win:
        basis = win.receipt_json.get("authority_basis") or {}
        ck("the receipt records EARNED authority lineage (not a fixture)", basis.get("earned") is True)
        ck("the winner's basis NAMES the classified eCFR provenance (ecfr.gov → source_of_law)",
           "ecfr.gov" in basis.get("winner", "") and "source_of_law" in basis.get("winner", ""))
        ck("the held-out FAQ's basis records it earned no authority (unverified)",
           "unverified" in basis.get("held_out", ""))

    # 3. THE DECISIVE PROOF — flip the publisher: republish Reg-E on a vendor blog → it STOPS winning by authority.
    for a in built["artifacts"]:
        if a.artifact_id == built["reg_e_id"]:
            a.payload_json["publisher"] = "Acme Compliance LLC"
            a.payload_json["source_uri"] = "https://acme-compliance.example.com/reg-e"
            a.payload_json["source_signed"] = False
    rec_flipped = RC.reconcile(conflicts, by_id, tenant_id="acme")  # same conflict, mutated provenance
    win2 = _authority_winner(rec_flipped)
    ck("FLIP: Reg-E republished on a vendor blog NO LONGER wins by authority (authority is EARNED)",
       win2 is None or win2.winning_artifact_id != built["reg_e_id"])

    # 4. MULTI-SOURCE CORROBORATION — "independent authorities AGREE", not just "a source says". Earned, not asserted.
    two_indep = SA.corroboration([
        {"value": "blocked", "source_uri": "https://ofac.treasury.gov/x"},
        {"value": "blocked", "source_uri": "https://www.federalregister.gov/designation"}])
    ck("two INDEPENDENT authoritative sources agreeing → CORROBORATED",
       two_indep["corroborated"] and two_indep["independent_authoritative_sources"] == 2)
    same_src = SA.corroboration([
        {"value": "blocked", "source_uri": "https://ofac.treasury.gov/a"},
        {"value": "blocked", "source_uri": "https://ofac.treasury.gov/b"}])
    ck("the SAME authority twice is NOT corroboration (one independent domain)",
       not same_src["corroborated"] and same_src["independent_authoritative_sources"] == 1)
    one_plus_blog = SA.corroboration([
        {"value": "blocked", "source_uri": "https://ofac.treasury.gov/a"},
        {"value": "blocked", "source_uri": "https://rumor-blog.example.com/b"}])
    ck("a vendor blog does NOT corroborate an authoritative source (only authoritative tiers count)",
       not one_plus_blog["corroborated"] and one_plus_blog["independent_authoritative_sources"] == 1)
    disagree = SA.corroboration([
        {"value": "blocked", "source_uri": "https://ofac.treasury.gov/a"},
        {"value": "clear", "source_uri": "https://rumor-blog.example.com/b"}])
    ck("on disagreement the higher-authority value wins; corroboration counts only sources asserting IT",
       disagree["value"] == "blocked" and not disagree["corroborated"])

    print(("PASS — " if not fails else "FAIL — ")
          + "check_source_authority: authority is DERIVED from publisher/domain+provenance and recorded in the "
            "receipt; Reg-E's win is contingent on its eCFR provenance — flip the publisher and it stops winning.")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
