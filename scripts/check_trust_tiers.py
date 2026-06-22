#!/usr/bin/env python3
"""check_trust_tiers — the trust-agnostic seam: the trust tier gates execution environment + data flow (load-bearing).

Proves: curated may run on customer data unsandboxed; a DISCOVERED component may NOT touch customer data (synthetic only,
hard sandbox); an unknown/missing tier is denied by default (deny-by-default = discovery≠trust operational); the required
sandbox escalates with lower trust. serves_truth=false.

  python3 scripts/check_trust_tiers.py --self-test
"""
from __future__ import annotations

from src.teleon.runtime import trust_tiers as TT


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck("curated may run on CUSTOMER data, unsandboxed", TT.can_execute("curated", "customer")["allowed"] and TT.required_sandbox("curated") == "none")
    disc = TT.can_execute("discovered", "customer")
    ck("a DISCOVERED component may NOT touch customer data (synthetic only)", disc["allowed"] is False and "may not run" in disc["reason"])
    ck("a discovered component CAN run on synthetic data — in a HARD sandbox", TT.can_execute("discovered", "synthetic")["allowed"] and TT.required_sandbox("discovered") == "hard")
    ck("community may run on internal but NOT customer data, sandboxed in a container",
       TT.can_execute("community", "internal")["allowed"] and not TT.can_execute("community", "customer")["allowed"] and TT.required_sandbox("community") == "container")
    ck("an UNKNOWN tier is denied by default (deny-by-default = discovery≠trust)", TT.can_execute("totally_unknown", "public")["allowed"] is False)
    ck("a component with no trust_tier defaults to the most restrictive (experimental), denied on customer data",
       TT.tier_of({"component_id": "x"}) == "experimental" and TT.gate_component({"component_id": "x"}, "customer")["allowed"] is False)
    ck("the sandbox escalates as trust drops (none < container < hard)",
       [TT.required_sandbox(t) for t in ("curated", "community", "discovered")] == ["none", "container", "hard"])
    ck("serves_truth=false", disc["serves_truth"] is False)

    print("\n" + ("PASS - check_trust_tiers: the trust tier gates execution sandbox + data flow; discovered/experimental "
                  "are synthetic-only in a hard sandbox; deny-by-default." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
