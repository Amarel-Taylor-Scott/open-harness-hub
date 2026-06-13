#!/usr/bin/env python3
"""scripts.check_company_portfolio_boundaries — PROOF: the COMPANY boundary model is well-formed, internally
safe, and CONSISTENT with the import dependency law.

Portfolio (owner-directed 2026-06-06): HoldCo **AI Done Right** (parent display name; slug/company_id stays
`contextiseverything`; tagline "Context. Capability. Proof."; canonical architecture/brand.json) owns Teleon (runtime
SaaS), Baltor (applied product, a tenant of Teleon), and OpenHarnessHub (open ecosystem). Sources:
architecture/company_portfolio_map.json (this model) + architecture/portfolio_dependency_law.json (import law)
+ architecture/domain_brand_risk_register.json (brand risk).

Asserts:
  A. WELL-FORMED: holding_company == 'contextiseverything'; the tracked company-boundary entities are present;
     principle + located_close_means + repo_evolution_phases recorded; each entity has the required boundary fields.
  B. HOLDCO OWNS NO RUNTIME / NO CUSTOMER DATA: contextiseverything.owned_runtime_surfaces == [] and forbids
     customer_data + runtime data (the holding company is never a runtime).
  C. CONSISTENT WITH THE IMPORT LAW (no contradiction): each company's owned_runtime_surfaces == the dependency
     law's package_roots for that layer; allowed_integrations == may_depend_on for that layer.
  D. DATA SEPARATION (trust): every sensitive_truth_type is owned by EXACTLY ONE company (Baltor) and appears in
     every OTHER company's forbidden_data_types — Teleon/OHH/HoldCo can never own or store Baltor truth.
  E. UNIQUENESS: local_dev_port is unique across companies (no collision); website_domains are disjoint across
     companies (brand separation); Baltor's port matches the running admin server port read from
     local_service_registry (baltor_admin_demo_server) — single-sourced, never a literal here.
  F. SHARED FOUNDATION: 'production database' + 'god token' + 'customer data store' are in never_shared and NOT
     in shared (no shared prod DB / no god token).
  G. BRAND RISK: the register flags AI Done Right (parent; conflict_caution, clearance_pending) with required
     checks, and Teleon (owned teleon.dev) with the teleon.ai caution + positioning guard.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_A = _REPO / "architecture"
_REQUIRED_FIELDS = ("company_id", "role", "product_boundary", "website_domains", "owned_runtime_surfaces",
                    "owned_data_types", "forbidden_data_types", "allowed_integrations", "shared_contracts",
                    "deployment_profile", "local_dev_port", "cloud_account_strategy", "separation_level")


def _registry_port(service_id: str) -> int:
    """SINGLE SOURCE: the running admin/Baltor port comes from the service registry, never a literal
    here — a port typed twice is a port that drifts (it did: 9307 vs the registry's 9301), and a
    check that compares the map to a sibling literal locks the drift in instead of catching it."""
    reg = json.loads((_A / "local_service_registry.json").read_text())
    for s in reg.get("services", []):
        if s.get("service_id") == service_id:
            return int(s["port"])
    raise SystemExit(f"check_company_portfolio_boundaries: '{service_id}' not in local_service_registry")


_BALTOR_ADMIN_PORT = _registry_port("baltor_admin_demo_server")  # derived from the registry, not hand-typed


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    pmap = json.loads((_A / "company_portfolio_map.json").read_text())
    law = json.loads((_A / "portfolio_dependency_law.json").read_text())
    risk = json.loads((_A / "domain_brand_risk_register.json").read_text())
    companies = pmap["companies"]

    # A. well-formed
    check("A: holding_company is contextiseverything", pmap.get("holding_company") == "contextiseverything")
    check("A: tracked company-boundary entities present",
          set(companies) == {"contextiseverything", "teleon", "baltor", "openharnesshub",
                             "opencontexthub", "openskillshub", "opentoolshub",
                             "openbenchmarkhub", "openmcphub", "opencompressionhub"}, str(sorted(companies)))
    check("A: principle + located_close_means + repo_evolution_phases recorded",
          bool(pmap.get("principle")) and len(pmap.get("located_close_means", [])) >= 3 and len(pmap.get("repo_evolution_phases", [])) >= 2)
    for cid, c in companies.items():
        missing = [f for f in _REQUIRED_FIELDS if f not in c]
        check(f"A: {cid} has all boundary fields", not missing, f"missing {missing}")

    # B. HoldCo owns no runtime / no customer data
    hc = companies["contextiseverything"]
    check("B: HoldCo owns NO runtime surfaces", hc["owned_runtime_surfaces"] == [], str(hc["owned_runtime_surfaces"]))
    check("B: HoldCo forbids customer_data + runtime data",
          "customer_data" in hc["forbidden_data_types"] and any("runtime" in f or "capability_task_run" in f for f in hc["forbidden_data_types"]))

    # C. consistent with the import law
    law_layers = law["layers"]
    layer_of = {"teleon": "teleon", "baltor": "baltor", "openharnesshub": "openharnesshub"}
    for cid, ln in layer_of.items():
        check(f"C: {cid} owned_runtime_surfaces == import-law package_roots",
              companies[cid]["owned_runtime_surfaces"] == law_layers[ln]["package_roots"],
              f'{companies[cid]["owned_runtime_surfaces"]} vs {law_layers[ln]["package_roots"]}')
        check(f"C: {cid} allowed_integrations == import-law may_depend_on",
              sorted(companies[cid]["allowed_integrations"]) == sorted(law_layers[ln]["may_depend_on"]),
              f'{companies[cid]["allowed_integrations"]} vs {law_layers[ln]["may_depend_on"]}')
    check("C: HoldCo has no import-law layer (owns no runtime)", "contextiseverything" not in law_layers)

    # D. data separation — sensitive truth owned by exactly Baltor, forbidden everywhere else
    sensitive = pmap["sensitive_truth_types"]
    for t in sensitive:
        owners = [cid for cid, c in companies.items() if t in c["owned_data_types"]]
        check(f"D: '{t}' owned by exactly Baltor", owners == ["baltor"], f"owners={owners}")
        others_ok = all(t in companies[cid]["forbidden_data_types"] for cid in companies if cid != "baltor")
        check(f"D: '{t}' forbidden in every non-Baltor company", others_ok)

    # E. uniqueness
    ports = [c["local_dev_port"] for c in companies.values()]
    check("E: local_dev_port unique across companies", len(ports) == len(set(ports)), str(ports))
    check(f"E: Baltor local_dev_port matches the registry admin port ({_BALTOR_ADMIN_PORT}, from baltor_admin_demo_server)",
          companies["baltor"]["local_dev_port"] == _BALTOR_ADMIN_PORT, str(companies["baltor"]["local_dev_port"]))
    all_domains = [d for c in companies.values() for d in c["website_domains"]]
    check("E: website_domains disjoint across companies (brand separation)", len(all_domains) == len(set(all_domains)), str(all_domains))

    # F. shared foundation — no shared prod DB / god token
    shared = set(pmap["shared_foundation"]["shared"])
    never = set(pmap["shared_foundation"]["never_shared"])
    for must_never in ("production database", "god token", "customer data store"):
        check(f"F: '{must_never}' is never_shared (not shared)", must_never in never and must_never not in shared)

    # G. brand risk register
    by_name = {e["name"]: e for e in risk["entries"]}
    cie = by_name.get("AI Done Right", {})
    check("G: AI Done Right (parent) flagged conflict_caution + clearance_pending + required_checks",
          cie.get("status") == "conflict_caution" and cie.get("clearance_pending") is True and len(cie.get("required_checks", [])) >= 1)
    tel = by_name.get("Teleon", {})
    check("G: Teleon owns teleon.dev + flags teleon.ai caution + positioning guard",
          "teleon.dev" in tel.get("owned", []) and any("teleon.ai" in c for c in tel.get("conflicts", [])) and len(tel.get("positioning_guard", [])) >= 1)

    print("\n" + ("PASS — check_company_portfolio_boundaries: the company boundary model is well-formed, consistent "
                  "with the import dependency law (surfaces + integrations agree), data-separated (Baltor truth is "
                  "owned by Baltor alone and forbidden everywhere else), the HoldCo owns no runtime/customer data, "
                  "no shared prod DB / god token, ports + domains are distinct, and the brand/domain risks are "
                  "registered." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_company_portfolio_boundaries.py --self-test")
    raise SystemExit(0)
