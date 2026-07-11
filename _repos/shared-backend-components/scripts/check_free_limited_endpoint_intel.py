#!/usr/bin/env python3
"""scripts.check_free_limited_endpoint_intel — PROOF: the Free/Limited LLM Endpoint Intelligence layer classifies
endpoints + repos by governance class, scores risk, and gates promotion — honestly and deterministically.

Asserts:
  A. CONTRACTS: FreeLimitedEndpoint + EndpointDueDiligenceReport + GatewayRepoAssessment registered.
  B. REGISTRY: official candidates seeded; EVERY rate_limit_claim is owner_provided_unverified (confidence
     'unverified') — third-party free-tier claims are never trusted.
  C. CLAWLESS: classified browser_agent_runtime (700), NOT an LLM endpoint / inference provider; sandbox-gated.
  D. OFFICIAL FREE TIER → candidate: GitHub Models / Groq → class 100, teleon_use candidate_non_serving,
     baltor_use candidate_only_not_truth, recommended_phase in [1,3] (not rejected, not production-by-default).
  E. DISCOVERY LIST → metadata_only (600), executable never, phase 0.
  F. GATEWAY REPO → lab_candidate_only (500), import_allowed False.
  G. SHARED-KEY / REVERSE-ENGINEERED → quarantine (>= quarantine_floor).
  H. TOGETHER AI → paid_required (300), NOT free (guards the stale 'free credit' trap).
  I. RISK SCORING deterministic; quarantine pins risk to 100.
  J. OFFICIAL-CLAIM-WITHOUT-DOCS → unknown_quarantine (990), phase -1 (cannot reach candidate).
  K. OPENTOOLSHUB projection is metadata-only: executable False, gated through the Inference Gateway.
  L. PROVIDER NODE = PROPOSAL only: requires secret_ref + local_equivalent + receipt; NOT written to the graph.
  M. REDTEAM: shared-key-described-as-official → still quarantine; ClawLess-as-endpoint → still runtime;
     free-tier + customer_sensitive → denied; raw key → forced quarantine + never echoed; output is never truth.
  N. DETERMINISM + composes the Inference Gateway + dependency law (no src.baltor import).

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.inference import free_endpoint_intel as FE
from src.teleon.inference import oips as OIPS


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    A = _resource("architecture")
    contracts = json.dumps(json.loads((A / "contract_registry.json").read_text()))
    check("A: 3 contracts registered", all(s in contracts for s in (
        "inference/FreeLimitedEndpoint.schema.json", "inference/EndpointDueDiligenceReport.schema.json",
        "inference/GatewayRepoAssessment.schema.json")))

    reg = json.loads((A / "free_limited_llm_endpoint_registry.json").read_text())["endpoints"]
    reports = {r["endpoint_id"]: r for r in FE.run_registry()}
    check("B: official candidates seeded (>=9) + every rate_limit_claim unverified",
          len(reg) >= 9 and all(e.get("rate_limit_claim", {}).get("confidence") == "unverified"
                                for e in reg if "rate_limit_claim" in e))
    # cross-check: derived class matches the seeded class_code for every row
    derived_ok = all(reports[e["endpoint_id"]]["class_code"] == e["class_code"] for e in reg)
    check("B: derived class == seeded class for every registry row", derived_ok,
          str({e["endpoint_id"]: (e["class_code"], reports[e["endpoint_id"]]["class_code"]) for e in reg
               if reports[e["endpoint_id"]]["class_code"] != e["class_code"]}))

    wl = FE.run_watchlist()
    by_repo = {r["repo_id"]: r for r in wl}
    claw = by_repo.get("open-gitagent/clawless", {})
    check("C: ClawLess -> browser_agent_runtime, NOT an inference provider, sandbox-gated",
          claw.get("class_code") == 700 and claw.get("is_inference_provider") is False
          and claw.get("executable") == "sandbox_gateway_only", json.dumps(claw))

    gh = reports.get("endpoint.github_models@candidate", {})
    gq = reports.get("endpoint.groq@candidate", {})
    check("D: GitHub Models + Groq -> class 100 candidate (non-serving, not truth), phase in [1,3]",
          gh.get("class_code") == 100 and gq.get("class_code") == 100
          and gh.get("teleon_use") == "candidate_non_serving" and gh.get("baltor_use") == "candidate_only_not_truth"
          and 1 <= gh.get("recommended_phase", -9) <= 3 and 1 <= gq.get("recommended_phase", -9) <= 3,
          json.dumps(gh))

    disc = by_repo.get("cheahjs/free-llm-api-resources", {})
    check("E: discovery list -> metadata_only (600), executable never, phase 0",
          disc.get("class_code") == 600 and disc.get("executable") == "never" and disc.get("recommended_phase") == 0,
          json.dumps(disc))

    gw = by_repo.get("tashfeenahmed/freellmapi", {})
    check("F: gateway repo -> lab_candidate_only (500), import_allowed False",
          gw.get("class_code") == 500 and gw.get("role") == "lab_candidate_only" and gw.get("import_allowed") is False,
          json.dumps(gw))

    sk = by_repo.get("synthetic.shared_key_repo", {})
    rev = by_repo.get("synthetic.reverse_engineered_access", {})
    floor = FE._quarantine_floor()
    check("G: shared-key + reverse-engineered -> quarantine (>= floor)",
          sk.get("class_code", 0) >= floor and rev.get("class_code", 0) >= floor, f"{sk.get('class_code')},{rev.get('class_code')}")

    tg = reports.get("endpoint.together_ai@paid", {})
    check("H: Together AI -> paid_required (300), not free", tg.get("class_code") == 300, json.dumps(tg))

    r1, d1 = FE.score_risk(100, {"has_official_docs": True, "rate_limit_documented": True})
    r2, d2 = FE.score_risk(100, {"has_official_docs": True, "rate_limit_documented": True})
    rq, _ = FE.score_risk(900, {})
    check("I: risk deterministic + quarantine pins to 100", (r1, d1) == (r2, d2) and rq == 100)

    nodoc = FE.due_diligence({"endpoint_id": "endpoint.mystery@x", "signals": {"has_official_docs": False}})
    check("J: official-claim-without-docs -> unknown_quarantine (990), phase -1",
          nodoc["class_code"] == 990 and nodoc["recommended_phase"] == -1, json.dumps(nodoc))

    meta = FE.to_opentools_metadata(gh)
    check("K: OpenToolsHub projection metadata-only (not executable, gated via gateway)",
          meta["executable"] is False and meta["executable_use_gated_through"] == "teleon_inference_gateway"
          and meta["secret_policy"] == "secret_ref_only_no_raw_keys")

    prop = gh.get("provider_node_proposal") or {}
    graph_ids = {n["node_id"] for n in OIPS.load_graph()["nodes"]}
    check("L: provider node is a PROPOSAL (secret_ref+local_equivalent+receipt; not in graph)",
          prop.get("written_to_graph") is False and prop.get("secret_ref_required") is True
          and prop.get("local_equivalent") == OIPS.OFFLINE_DEFAULT_NODE and prop.get("receipt_required") is True
          and prop.get("proposed_node_id") not in graph_ids, json.dumps(prop))

    # ── REDTEAM ──
    rt_sharedkey = FE.assess_gateway_repo({"repo_id": "rt.fake", "role": "self_hosted_gateway",
                                           "signals": {"has_official_docs": True, "shared_key_markers": True}})
    check("M1: shared-key repo dressed as 'official' -> still quarantine", rt_sharedkey["class_code"] >= floor)
    rt_claw = FE.due_diligence({"endpoint_id": "rt.claw_as_endpoint",
                                "signals": {"has_official_docs": True, "browser_runtime": True}})
    check("M2: ClawLess-as-free-endpoint -> still browser runtime, not a provider",
          rt_claw["class_code"] == 700 and rt_claw["is_inference_provider"] is False)
    pol100 = json.loads((A / "free_limited_llm_endpoint_policy.json").read_text())["by_class"]["100"]
    check("M3: free-tier + customer_sensitive -> denied",
          pol100["customer_sensitive_allowed"] is False and gh["allowed_data_class"] != "customer_sensitive")
    fake_key = "sk-" + "A" * 30  # built dynamically; never a real/literal key
    rt_key = FE.due_diligence({"endpoint_id": "rt.leaky", "signals": {"has_official_docs": True}, "leak": fake_key})
    check("M4: raw key -> forced quarantine, detected, proposal None, key NOT echoed in report",
          rt_key["raw_key_detected"] is True and rt_key["class_code"] >= floor
          and rt_key["provider_node_proposal"] is None and fake_key not in json.dumps(rt_key))
    check("M5: NOTHING is truth (every endpoint + repo report is_truth False)",
          all(r["is_truth"] is False for r in reports.values()) and all(r["is_truth"] is False for r in wl)
          and rt_claw["is_truth"] is False)

    check("N: deterministic over the registry", {r["endpoint_id"]: r for r in FE.run_registry()} == reports)
    src = (_resource("src/teleon/inference/free_endpoint_intel.py")).read_text()
    check("N: composes the Inference Gateway (imports oips)", "from src.teleon.inference import oips" in src)
    check("N: no src.baltor import (dependency law)",
          not any(l.strip().startswith(("import src.baltor", "from src.baltor")) for l in src.splitlines()))

    print("\n" + ("PASS — check_free_limited_endpoint_intel: official free/limited endpoints register as candidates "
                  "(non-serving, not truth, phase-capped); discovery lists are metadata-only; gateway repos are "
                  "lab-candidates; ClawLess is a browser runtime (not an LLM endpoint); shared-key/bypass/"
                  "reverse-engineered/no-docs/raw-key are quarantined; Together is paid; provider nodes are "
                  "proposals only; all advisory, never truth; via the Inference Gateway; deterministic."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_free_limited_endpoint_intel.py --self-test")
    raise SystemExit(0)
