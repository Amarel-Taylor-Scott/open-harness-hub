#!/usr/bin/env python3
"""check_teleon_endpoint_registry — proof that interchangeable provider ENDPOINTS are selected by objective.

When a Teleon unit needs e.g. WHOIS, many providers can serve it (RDAP, a paid API, a library). This proves the
objective layer picks the right one per priority, governs it, and improves it:
  * minimize_cost -> a free endpoint; minimize_latency -> the fastest; maximize_accuracy -> the most reliable —
    so the SAME capability resolves to DIFFERENT endpoints under different priorities (a traceable SelectionTrace).
  * SAFETY beats objective: a forbidden endpoint (the org policy bans its license/domain) is excluded even if it
    would win; all-forbidden fails loud (escalate, never a silent wrong pick).
  * TELEMETRY refines the choice: an endpoint observed to be slow is deprioritized on the next selection.
  * never serves truth; deterministic.

CLI: python3 scripts/check_teleon_endpoint_registry.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.endpoints import endpoints_for, registered_capabilities, select_endpoint
from src.teleon.objectives import PRESETS, ObjectiveError, RunLedger, RunObservation


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    caps = registered_capabilities()
    ck("the endpoint registry covers several capabilities (whois, geocode, stock, weather)",
       {"whois-domain-lookup", "geocode-address", "stock-price-quote", "weather-current"} <= set(caps), str(caps))

    eps = {e.endpoint_id: e for e in endpoints_for("whois-domain-lookup")}
    pick = lambda obj, **kw: select_endpoint("whois-domain-lookup", PRESETS[obj], **kw)["chosen"]

    # objective drives the choice across cost / latency / reliability.
    cost_pick, lat_pick, acc_pick = pick("minimize_cost"), pick("minimize_latency"), pick("maximize_accuracy")
    ck("minimize_cost picks a FREE WHOIS endpoint (cost 0.0)", eps[cost_pick].cost == 0.0, cost_pick)
    ck("minimize_latency picks the FASTEST WHOIS endpoint",
       eps[lat_pick].latency_ms == min(e.latency_ms for e in eps.values()), f"{lat_pick} {eps[lat_pick].latency_ms}ms")
    ck("maximize_accuracy picks the MOST RELIABLE WHOIS endpoint (the paid API)",
       eps[acc_pick].reliability == max(e.reliability for e in eps.values()), f"{acc_pick} {eps[acc_pick].reliability}")
    ck("the SAME capability resolves to DIFFERENT endpoints under different priorities",
       len({cost_pick, lat_pick, acc_pick}) >= 2, f"{cost_pick}/{lat_pick}/{acc_pick}")

    # traceable + deterministic + never truth
    trace = select_endpoint("whois-domain-lookup", PRESETS["minimize_latency"])
    ck("the endpoint selection is a full SelectionTrace with the chosen endpoint detail, never truth",
       len(trace["ranked"]) == len(eps) and trace["chosen_endpoint"]["endpoint_id"] == trace["chosen"]
       and trace["serves_truth"] is False and bool(trace["rationale"]))
    ck("endpoint selection is deterministic",
       select_endpoint("whois-domain-lookup", PRESETS["minimize_latency"])["chosen"] == trace["chosen"])

    # SAFETY beats objective: forbid the accuracy winner -> excluded, a different allowed endpoint wins.
    safe = select_endpoint("whois-domain-lookup", PRESETS["maximize_accuracy"], forbidden={acc_pick})
    ck("a forbidden endpoint (org policy) is EXCLUDED even when it would win (safety beats objective)",
       safe["chosen"] != acc_pick and acc_pick in safe["excluded_forbidden"])
    # all endpoints forbidden -> fail loud
    raised = False
    try:
        select_endpoint("whois-domain-lookup", PRESETS["balanced"], forbidden={e for e in eps})
    except ObjectiveError:
        raised = True
    ck("forbidding every endpoint fails loud (escalate, never a silent pick)", raised)

    # an unknown capability fails loud
    raised2 = False
    try:
        select_endpoint("no-such-capability", PRESETS["balanced"])
    except Exception:
        raised2 = True
    ck("selecting for an unregistered capability fails loud", raised2)

    # TELEMETRY refines: the declared-fastest endpoint, observed SLOW, is no longer chosen for minimize_latency.
    led = RunLedger()
    for _ in range(8):  # many observations dominate the declared prior
        led.record(RunObservation(lat_pick, cost=0.0, latency_ms=9000, llm_calls=0, passed=True, output_key="ok"))
    lat_pick_obs = select_endpoint("whois-domain-lookup", PRESETS["minimize_latency"], ledger=led)["chosen"]
    ck("observed telemetry deprioritizes an endpoint that turned out slow (self-improving selection)",
       lat_pick_obs != lat_pick, f"declared={lat_pick} observed-aware={lat_pick_obs}")

    # geocode sanity: minimize_cost -> free; maximize_accuracy -> the most reliable (Google).
    g = {e.endpoint_id: e for e in endpoints_for("geocode-address")}
    gcost = select_endpoint("geocode-address", PRESETS["minimize_cost"])["chosen"]
    gacc = select_endpoint("geocode-address", PRESETS["maximize_accuracy"])["chosen"]
    ck("geocode minimize_cost -> a free endpoint; maximize_accuracy -> the most reliable",
       g[gcost].cost == 0.0 and g[gacc].reliability == max(e.reliability for e in g.values()), f"{gcost}/{gacc}")

    print("\n" + ("PASS - check_teleon_endpoint_registry: a capability's interchangeable provider endpoints are "
                  "selected by the objective layer (minimize_cost -> free, minimize_latency -> fastest, "
                  "maximize_accuracy -> most reliable; same capability, different endpoint per priority); a "
                  "policy-forbidden endpoint is excluded before scoring (safety beats objective) and all-forbidden "
                  "fails loud; observed telemetry deprioritizes an endpoint that turned out slow. Deterministic, never truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
