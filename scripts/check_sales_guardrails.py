#!/usr/bin/env python3
"""scripts.check_sales_guardrails — PROOF (redteam): the sales/lead-proof system's SAFETY GATE blocks the
dangerous behaviors before any outward-facing tool is built. Diagnostics describe observed patterns; they never
become legal conclusions or public accusations against named real companies without review.

Asserts (all dangerous patterns FAIL SAFELY):
  A. CONTRACTS: EvidencePack/TargetCompany/DiagnosticRun/ReviewApproval registered.
  B. CLAIM LANGUAGE: 'illegal'/'breaking the law' -> legal_conclusion; 'appears unsafe, requires review' -> safe.
  C. SAFE REWRITE: a legal-conclusion sentence rewrites to non-legal-conclusion ('appears'/'requires review').
  D. NAMED REAL COMPANY: a public_claim_safe pack about a named real company WITHOUT approval -> NOT publishable.
  E. LEGAL CONCLUSION: a pack whose claim text asserts a legal conclusion -> NOT publishable.
  F. REGULATED CATEGORY: a finance pack public_claim_safe without approved review -> NOT publishable.
  G. PROVENANCE: a pack with no source/authorization -> NOT publishable.
  H. AUTHORIZATION: a LIVE third-party probe without written_authorization -> blocked; customer_provided -> ok.
  I. OUTREACH: auto_send / missing opt-out / legal-conclusion body -> blocked; draft_only+opt_out+safe -> ok.
  J. PRODUCT MESSAGE: Baltor 'legal advice' blocked; Teleon 'replaces Kubernetes' blocked.
  K. SEEDS: the committed target seed fixture is SYNTHETIC only (no real company seeded without approval).
  L. SAFE PATH: a synthetic, safe-language, provenanced, non-public pack -> publishable/ok.
  M. DETERMINISM + dependency law placement.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.sales import claim_guard as G

_NOW = "2026-06-07T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    contracts = json.dumps(json.loads((_REPO / "architecture" / "contract_registry.json").read_text()))
    check("A: 4 sales contracts registered", all(f"sales/{s}.schema.json" in contracts for s in
          ("EvidencePack", "TargetCompany", "DiagnosticRun", "ReviewApproval")))

    check("B: 'illegal' -> legal_conclusion", G.classify_claim_language("their chatbot is illegal")["class"] == "legal_conclusion")
    check("B: 'appears unsafe, requires review' -> safe", G.classify_claim_language("the answer appears unsafe and requires review")["class"] == "safe")

    rw = G.safe_rewrite("This is illegal and violates the law")
    check("C: safe_rewrite removes the legal conclusion", G.classify_claim_language(rw)["class"] != "legal_conclusion", rw)

    base = {"evidence_pack_id": "ep1", "company_id": "c", "target_product": "Baltor", "pain_hypothesis": "stale_context",
            "observed_artifacts": [{"summary": "answer appears stale"}], "source_urls": ["https://example.com/x"],
            "risk_categories": ["stale_context"], "confidence": "low", "public_claim_safe": False,
            "requires_legal_review": False, "review_status": "not_required", "claim_language_class": "safe",
            "company_is_synthetic": True, "authorization_basis": "public_static_metadata", "created_at": _NOW}

    named_public = dict(base, company_is_synthetic=False, public_claim_safe=True)
    ok_d, why_d = G.gate_evidence_pack(named_public)
    check("D: named real company + public claim w/o approval -> NOT publishable", not ok_d and "named_real_company_public_claim_without_approval" in why_d)

    legal_pack = dict(base, observed_artifacts=[{"summary": "the company is breaking the law"}])
    ok_e, why_e = G.gate_evidence_pack(legal_pack)
    check("E: legal-conclusion claim -> NOT publishable", not ok_e and "contains_legal_conclusion" in why_e)

    fin_public = dict(base, pain_hypothesis="unsafe_financial_guidance", risk_categories=["unsafe_financial_guidance"],
                      company_is_synthetic=False, public_claim_safe=True, requires_legal_review=True, review_status="pending")
    ok_f, why_f = G.gate_evidence_pack(fin_public)
    check("F: regulated public claim w/o approved review -> NOT publishable", not ok_f and "regulated_public_claim_requires_approved_review" in why_f)

    noprov = dict(base, source_urls=[], authorization_basis=None)
    ok_g, why_g = G.gate_evidence_pack(noprov)
    check("G: missing source/authorization -> NOT publishable", not ok_g and "missing_source_or_authorization" in why_g)

    ok_h1, why_h1 = G.authorization_ok({"is_live_probe": True, "authorization_basis": "public_static_metadata"})
    ok_h2, _ = G.authorization_ok({"is_live_probe": False, "authorization_basis": "customer_provided"})
    check("H: live probe w/o written authorization blocked; customer_provided ok",
          (not ok_h1) and "live_probe_requires_written_authorization" in why_h1 and ok_h2)

    ok_i1, why_i1 = G.gate_outreach({"auto_send": True, "opt_out": True, "body": "hi"})
    ok_i2, _ = G.gate_outreach({"mode": "draft_only", "opt_out": True, "body": "Your answer appears to require review."})
    check("I: auto_send blocked; draft_only+opt_out+safe ok", (not ok_i1) and "auto_send" in " ".join(why_i1) and ok_i2)

    okj1, _ = G.product_message_ok("Baltor", "Baltor gives you legal advice")
    okj2, _ = G.product_message_ok("Teleon", "Teleon replaces Kubernetes")
    check("J: forbidden product claims blocked (Baltor legal advice / Teleon replaces K8s)", (not okj1) and (not okj2))

    seeds = json.loads((_REPO / "fixtures" / "sales" / "synthetic_targets_seed.json").read_text())["targets"]
    check("K: committed target seeds are synthetic only", all(t.get("is_synthetic") for t in seeds) and seeds)

    ok_l, why_l = G.gate_evidence_pack(base)
    check("L: synthetic + safe + provenanced + non-public pack -> publishable", ok_l, str(why_l))

    check("M: deterministic", G.gate_evidence_pack(base) == (ok_l, why_l) and G.classify_claim_language("illegal") == G.classify_claim_language("illegal"))

    print("\n" + ("PASS — check_sales_guardrails: the sales safety gate blocks legal-conclusion language, public "
                  "accusations against named real companies without review, regulated public claims without "
                  "approved legal review, unprovenanced packs, unauthorized live third-party probes, auto-send "
                  "outreach, and forbidden product claims; safe synthetic packs pass; deterministic."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_sales_guardrails.py --self-test")
    raise SystemExit(0)
