#!/usr/bin/env python3
"""check_teleon_org_guardrail_policy — proof that org devops/security rules BOUND capability selection + repair.

Organizations only allow certain licenses, source domains, runtime classes, packages, or methodologies. This
proves the guardrail policy enforces those confines on BOTH the provider endpoints a unit may call AND the fixes
the AI may make when it self-heals/evolves a unit:
  * license deny-list / allow-list / strict-unknown; source-domain allow-list with wildcards; runtime-class
    allow-list; denied packages; methodology rules (deterministic_only, no_llm).
  * COMPOSES WITH ENDPOINT SELECTION: forbidden_endpoints feeds select_endpoint, so under a regulated policy the
    objective can only choose an ALLOWED provider (a banned-license/off-domain endpoint is excluded — safety
    beats objective), and an all-banned capability fails loud.
  * BOUNDS SELF-HEAL / EVOLUTION: under a deterministic-only org, the AI may heal/fork a unit ONLY to a
    deterministic runner — a model runner is VETOED (escalate to human) rather than crossing the org's confines.
  * deterministic; unknown policy fails loud; a decision never serves truth.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_org_guardrail_policy.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.endpoints import endpoints_for, select_endpoint
from src.teleon.evolution import RunnerNode
from src.teleon.governance import (
    OrgPolicyError,
    bounds_runner_change,
    evaluate_endpoint,
    forbidden_endpoints,
    load_policy,
    policy_ids,
)
from src.teleon.objectives import PRESETS, ObjectiveError


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    ck("the registry carries the example org policies", {"default-permissive", "regulated-financial-strict",
       "no-copyleft", "deterministic-audit"} <= set(policy_ids()))

    permissive = load_policy("default-permissive")
    regulated = load_policy("regulated-financial-strict")
    nocopyleft = load_policy("no-copyleft")
    audit = load_policy("deterministic-audit")

    whois = {e.endpoint_id: e for e in endpoints_for("whois-domain-lookup")}

    # default-permissive allows every endpoint.
    ck("default-permissive allows every WHOIS endpoint",
       all(evaluate_endpoint(e, permissive).allowed for e in whois.values()))

    # regulated: commercial license denied; non-allow-listed domain denied; gov/public+allow-listed domain allowed.
    ck("regulated DENIES the commercial paid API (license deny-list)",
       not evaluate_endpoint(whois["whoisxmlapi"], regulated).allowed)
    ck("regulated DENIES the library endpoint (off-allow-list domain / denied package)",
       not evaluate_endpoint(whois["python-whois-lib"], regulated).allowed)
    ck("regulated ALLOWS the official free RDAP endpoint (public license + allow-listed domain + deterministic)",
       evaluate_endpoint(whois["rdap-iana"], regulated).allowed,
       str(evaluate_endpoint(whois["rdap-iana"], regulated).reasons))

    # COMPOSITION with endpoint selection: under regulated, ANY objective resolves to the only allowed endpoint.
    forb = forbidden_endpoints("whois-domain-lookup", regulated)
    ck("forbidden_endpoints excludes the banned WHOIS providers (only RDAP remains)",
       forb == {"whoisxmlapi", "python-whois-lib"}, str(forb))
    for obj in ("minimize_cost", "minimize_latency", "maximize_accuracy"):
        chosen = select_endpoint("whois-domain-lookup", PRESETS[obj], forbidden=forb)["chosen"]
        ck(f"under regulated, {obj} can ONLY pick the allowed RDAP endpoint (safety beats objective)",
           chosen == "rdap-iana", chosen)

    # geocode under regulated: only the official Census endpoint survives.
    gforb = forbidden_endpoints("geocode-address", regulated)
    gchosen = select_endpoint("geocode-address", PRESETS["minimize_latency"], forbidden=gforb)["chosen"]
    ck("under regulated, geocoding resolves to the official Census endpoint (gov domain + public license)",
       gchosen == "census-geocoder", f"{gchosen} forb={gforb}")

    # an all-banned capability fails loud rather than silently picking a forbidden provider.
    raised = False
    try:
        select_endpoint("whois-domain-lookup", PRESETS["balanced"], forbidden=set(whois))
    except ObjectiveError:
        raised = True
    ck("if the org bans every provider for a capability, selection fails loud (escalate)", raised)

    # no-copyleft: AGPL/GPL denied, MIT allowed (endpoint license check).
    from src.teleon.endpoints import ProviderEndpoint
    agpl = ProviderEndpoint("x", "c", "p", "rest_api", "paid", 0.01, 100, 0.99, "AGPL-3.0", "ex.com")
    mit = ProviderEndpoint("y", "c", "p", "rest_api", "free", 0.0, 100, 0.95, "MIT", "ex.com")
    ck("no-copyleft DENIES an AGPL endpoint and ALLOWS an MIT one",
       not evaluate_endpoint(agpl, nocopyleft).allowed and evaluate_endpoint(mit, nocopyleft).allowed)
    ck("regulated (strict_unknown_license) DENIES an unknown-license endpoint",
       not evaluate_endpoint(ProviderEndpoint("z", "c", "p", "rest_api", "free", 0.0, 100, 0.9, "unknown", "x.gov"),
                             regulated).allowed)

    # BOUNDS SELF-HEAL / EVOLUTION: under deterministic-audit, the AI may fix a unit ONLY with a deterministic runner.
    model_runner = RunnerNode("m@v1", "cap", "model", tier=2, determinism=0.2, capability_coverage=1.0, cost=0.07)
    rule_runner = RunnerNode("r@v1", "cap", "distilled_rule", tier=1, determinism=1.0, capability_coverage=0.9)
    ck("deterministic-audit VETOES a self-heal/fork to a MODEL runner (not deterministic / uses an LLM)",
       not bounds_runner_change(model_runner, audit).allowed,
       str(bounds_runner_change(model_runner, audit).reasons))
    ck("deterministic-audit ALLOWS a self-heal/fork to a DETERMINISTIC rule runner",
       bounds_runner_change(rule_runner, audit).allowed)
    ck("regulated (deterministic_only) also VETOES the model runner as a fix",
       not bounds_runner_change(model_runner, regulated).allowed)
    ck("default-permissive allows ANY runner as a fix (no methodology constraint)",
       bounds_runner_change(model_runner, permissive).allowed)

    # runtime-class allow-list bounds a runner that declares an off-list runtime.
    offlist = {"determinism": 1.0, "kind": "distilled_rule", "runtime_class": "kubernetes-job"}
    ck("regulated VETOES a fix on an off-allow-list runtime class (only local-subprocess/queue-worker allowed)",
       not bounds_runner_change(offlist, regulated).allowed)

    # deterministic + fail loud + never truth
    ck("a policy decision never serves truth", evaluate_endpoint(whois["rdap-iana"], regulated).serves_truth is False)
    ck("evaluation is deterministic",
       evaluate_endpoint(whois["rdap-iana"], regulated).as_dict() == evaluate_endpoint(whois["rdap-iana"], regulated).as_dict())
    raised2 = False
    try:
        load_policy("no-such-policy")
    except OrgPolicyError:
        raised2 = True
    ck("an unknown policy id fails loud", raised2)

    print("\n" + ("PASS - check_teleon_org_guardrail_policy: an org's devops/security rules (license/domain/"
                  "runtime/package allow+deny lists + methodology requirements) BOUND a capability — disallowed "
                  "provider endpoints are excluded before objective selection (safety beats objective; all-banned "
                  "fails loud), and the AI may self-heal/fork a unit ONLY to a runner within the confines (a model "
                  "fix is vetoed under a deterministic-only org). Deterministic, fails loud, never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
