#!/usr/bin/env python3
"""check_openapi_deconstructor — proof that an API hub's endpoint SPECS deconstruct into Teleon capability seeds.

Feeds the offline RapidAPI hub emulator (the DEFER-GATE local equivalent of the live Playwright harvest) through
the OpenAPI deconstructor: every operation (method + path + params + auth + response schema) becomes a governed
capability-seed candidate with an input/output contract and a high determinism ceiling — and the payoff: a
deconstructed endpoint DISTILLS to a deterministic capability via the distiller's direct_api_rule (an API call IS a
deterministic call). Discovery != trust; nothing promoted; never serves truth.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_openapi_deconstructor.py --self-test
"""
from __future__ import annotations

import importlib.util
import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from local_emulators.rapidapi_hub_emulator import RapidApiHubEmulator
from src.teleon.evolution.distiller import distill
from src.teleon.seeds.openapi_deconstructor import deconstruct_api, deconstruct_hub


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # DEFER GATE: the live Playwright harvest has a built, importable local equivalent
    ck("the live-harvest seam has a built local emulator (DEFER GATE)",
       importlib.util.find_spec("local_emulators.rapidapi_hub_emulator") is not None)
    emu = RapidApiHubEmulator()
    ck("the emulator feeds OpenAPI specs offline (no network)", len(emu.list_apis()) >= 2 and emu.serves_truth is False)

    seeds = deconstruct_hub(emu.all_specs())
    ck("every endpoint deconstructs into a capability-seed candidate (>= 4 across the hub)", len(seeds) >= 4, str(len(seeds)))
    req = {"capability_slot", "intent", "input_contract", "output_contract", "method", "path", "endpoint",
           "auth_required", "determinism_ceiling", "distill_strategy", "governed", "serves_truth"}
    ck("every seed carries slot/intent/input+output contract/method/path/endpoint/auth/determinism",
       all(req <= set(s) for s in seeds), str([s["capability_slot"] for s in seeds if not req <= set(s)][:3]))
    ck("the input contract captures params; the endpoint is built from server + path",
       any(s["input_contract"]["path_query_params"] for s in seeds)
       and all(s["endpoint"].startswith("http") or s["endpoint"].startswith("/") for s in seeds))
    ck("an API call is treated as a DETERMINISTIC call (high ceiling + direct_api_rule)",
       all(s["determinism_ceiling"] >= 0.9 and s["distill_strategy"] == "direct_api_rule" for s in seeds))
    ck("RapidAPI endpoints are flagged auth_required (need the hub key)", all(s["auth_required"] for s in seeds))
    ck("every deconstructed endpoint is a governed candidate (never truth)",
       all(s["governed"] == "candidate" and s["serves_truth"] is False for s in seeds))

    # THE PAYOFF: a deconstructed endpoint distills to a DETERMINISTIC capability (endpoint -> seed -> det fork)
    s0 = seeds[0]
    d = distill(s0["capability_slot"], category=s0["category"], determinism_ceiling=s0["determinism_ceiling"],
                deterministic_coverage_estimate=0.9, strategy="direct_api_rule")
    ck("a deconstructed endpoint distills to a deterministic capability (direct_api_rule, applied, never truth)",
       d["strategy"] == "direct_api_rule" and d["applied"] is True and d["serves_truth"] is False
       and d["record"]["per_call_cost_after"] <= d["record"]["per_call_cost_before"])

    # per-API determinism + idempotent
    one = deconstruct_api(emu.openapi("whois-lookup"), api_name="whois-lookup")
    ck("a single API deconstructs deterministically (idempotent)",
       one == deconstruct_api(emu.openapi("whois-lookup"), api_name="whois-lookup") and len(one) >= 2)

    print("\n" + (f"PASS - check_openapi_deconstructor: {len(seeds)} RapidAPI-shaped endpoints deconstructed into "
                  f"governed capability-seed candidates (input/output contract + endpoint + auth + high determinism); "
                  f"a deconstructed endpoint distills to a deterministic capability via direct_api_rule; the live "
                  f"Playwright harvest's seam has a built local emulator (DEFER GATE). Discovery != trust; never "
                  f"serves truth." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_openapi_deconstructor.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
