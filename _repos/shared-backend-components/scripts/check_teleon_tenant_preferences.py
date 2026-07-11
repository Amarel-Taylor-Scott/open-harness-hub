#!/usr/bin/env python3
"""check_teleon_tenant_preferences — proof for the tunable preference / hard-blocker front door.

A tenant tunes the system; the layer compiles wishes to the proven machinery and enforces the distinction:
  * HARD constraints BLOCK (MIT-only license, vetted-only sources, no external egress) -> an OrgGuardrailPolicy
    that excludes disallowed providers/runners/forks before any selection (safety beats objective).
  * SOFT preferences RANK (objective_preset/weights -> a CapabilityObjective; axis_priorities surfaced).
  * accuracy.max_accuracy_drop tunes the A/B tolerance; SUGGESTIONS are advisory only.
It composes with endpoint selection + the A/B harness, and an unknown tenant gets the documented default.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_tenant_preferences.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.endpoints import ProviderEndpoint
from src.teleon.evolution import ab_test, ceiling_scorer
from src.teleon.governance import evaluate, evaluate_endpoint, forbidden_endpoints, preferences_for


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    bank = preferences_for("mit-only-bank")
    bank_policy = bank.to_org_policy()

    # SOFT preference -> objective; tolerance + priorities surfaced.
    ck("the soft objective compiles (mit-only-bank -> maximize_accuracy)", bank.to_objective().name == "maximize_accuracy")
    ck("the accuracy tolerance is tunable (bank is strict: max_accuracy_drop 0.01)", bank.max_accuracy_drop == 0.01)
    ck("axis priorities are surfaced (freshness first for the bank)",
       bank.axis_priorities[0] == "freshness" and bank.resolve()["serves_truth"] is False)

    # HARD: MIT-only LICENSE blocks copyleft + unknown; permissive license allowed.
    ck("HARD license blocker: a GPL provider is blocked, MIT is allowed",
       not evaluate({"license": "GPL-3.0", "vetted": True}, bank_policy).allowed
       and evaluate({"license": "MIT", "vetted": True}, bank_policy).allowed)
    ck("HARD: an unknown license is blocked for the bank (strict_unknown_license)",
       not evaluate({"license": "unknown", "vetted": True}, bank_policy).allowed)

    # HARD: VETTED-ONLY blocks an unvetted candidate even if its license is fine.
    ck("HARD vetted-only blocker: an MIT-but-UNVETTED candidate is blocked; MIT+vetted passes",
       not evaluate({"license": "MIT", "vetted": False}, bank_policy).allowed
       and evaluate({"license": "MIT", "vetted": True}, bank_policy).allowed)
    ck("vetted-only is enforced as a methodology in the compiled policy",
       "vetted_only" in bank_policy.required_methodologies)

    # strict-mit-airgapped: MIT ONLY (Apache blocked) + no external egress (cloud blocked).
    air = preferences_for("strict-mit-airgapped")
    air_policy = air.to_org_policy()
    ck("strict-mit: ONLY MIT is allowed (Apache-2.0 blocked)",
       evaluate({"license": "MIT", "vetted": True}, air_policy).allowed
       and not evaluate({"license": "Apache-2.0", "vetted": True}, air_policy).allowed)
    ck("airgapped: no_external_egress compiled from max_egress=local (a cloud domain is blocked)",
       "no_external_egress" in air_policy.required_methodologies
       and not evaluate({"license": "MIT", "vetted": True, "source_domain": "api.vendor.com"}, air_policy).allowed
       and evaluate({"license": "MIT", "vetted": True, "source_domain": "localhost"}, air_policy).allowed)

    # COMPOSES with endpoint selection: the cost-first tenant (no license blocker) — endpoints pass the license gate;
    # an AGPL endpoint would be blocked for the bank's policy.
    startup = preferences_for("cost-first-startup")
    ck("cost-first tenant: minimize_cost objective + lax tolerance (0.06) + no license blocker",
       startup.to_objective().name == "minimize_cost" and startup.max_accuracy_drop == 0.06
       and not startup.to_org_policy().allowed_licenses)
    agpl = ProviderEndpoint("agpl-ep", "c", "p", "rest_api", "paid", 0.01, 100, 0.99, "AGPL-3.0", "ex.com")
    ck("the bank's HARD license policy blocks an AGPL endpoint; the cost-first tenant does not",
       not evaluate_endpoint(agpl, bank_policy).allowed and evaluate_endpoint(agpl, startup.to_org_policy()).allowed)

    # COMPOSES with the A/B harness: preferences drive the policy + tolerance the A/B uses.
    cap = {"capability_slot": "stock-quote", "category": "financial-data", "determinism_ceiling": 1.0,
           "deterministic_coverage_estimate": 1.0}
    ab = ab_test(cap, scorer=ceiling_scorer, max_accuracy_drop=startup.max_accuracy_drop, policy=startup.to_org_policy())
    ck("the A/B harness runs under the tenant's compiled policy + tolerance (winner clears the tuned accuracy floor)",
       ab["winner_accuracy"] >= ab["accuracy_floor"] and ab["serves_truth"] is False)

    # unknown tenant -> documented default (no hard license blocker, balanced).
    d = preferences_for("some-unknown-tenant")
    ck("an unknown tenant gets the documented default (balanced, no hard license blocker)",
       d.to_objective().name == "balanced" and not d.to_org_policy().allowed_licenses)

    # suggestions are ADVISORY only (surfaced, never block).
    ck("suggestions are advisory (surfaced in resolve(), not enforced)",
       len(bank.resolve()["suggestions"]) >= 1)

    print("\n" + ("PASS - check_teleon_tenant_preferences: a tenant tunes soft objective + axis priorities + an "
                  "accuracy tolerance, sets HARD blockers (MIT-only license, vetted-only sources, no external "
                  "egress), and adds advisory suggestions; the layer COMPILES these to an OrgGuardrailPolicy (hard "
                  "blocks before selection) + a CapabilityObjective (soft ranks) + the A/B tolerance, composing with "
                  "endpoint selection + the A/B harness. Hard blocks, soft ranks, suggestions advise. Never truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
