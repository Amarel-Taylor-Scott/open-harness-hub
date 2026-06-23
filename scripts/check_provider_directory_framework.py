#!/usr/bin/env python3
"""check_provider_directory_framework — the vertical COMPOSES the shared framework (not a silo).

Proves: the provider-directory pipeline is retrieved as a shared TEMPLATE and mutated; it verifies via the SHARED verifier
(verify_buildable_dag) as a verified-working DAG of shared planes; it is costed by the SHARED simulator; and its economics
are written into the SHARED economic layer (telemetry write-back). serves_truth=false.

  python3 scripts/check_provider_directory_framework.py --self-test
"""
from __future__ import annotations

import uuid

from src.teleon.economics import economic_graph as EG
from src.teleon.verticals import provider_directory_capability as PDC

_SHARD = uuid.uuid4().hex[:12]   # isolate this check's economic store from concurrent subprocesses


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # retrieve-and-mutate via the SHARED template library
    comp = PDC.compose_from_template("keep our provider and practice directory accurate and up to date")
    ck("the vertical is retrieved as a SHARED template (provider_directory) and mutated", comp["matched"] and {n["step"] for n in comp["nodes"]} == {"acquire", "extract", "validate"})

    # verified by the SHARED verifier as a working DAG of shared planes
    v = PDC.verify()
    ck("the composed DAG is VERIFIED-WORKING via the shared verifier (search->field_parsing->validation)", v["verified_working"], str(v.get("type_incompatible_edges")) + str(v.get("unsatisfied_inputs")))

    # write the vertical's economics into the SHARED economic layer (telemetry write-back), then cost via the SHARED simulator
    PDC.record_baseline_economics(shard=_SHARD)
    ck("the vertical's component economics are in the SHARED economic layer (telemetry-backed, live)",
       EG.merged_economics("provider_sources", shard=_SHARD).get("live") is True)
    est = PDC.estimate(shard=_SHARD)
    ck("the SHARED simulator estimates the vertical's cost/latency over the economic graph", est["n_nodes"] == 3 and "total_cost" in est and "total_latency_ms" in est)
    ck("deterministic-first: the vertical's measured cost is ~0 (free registries + deterministic resolvers)", est["total_cost"] == 0.0)
    ck("serves_truth=false", v["serves_truth"] is False and est["serves_truth"] is False)

    print("\n" + ("PASS - check_provider_directory_framework: the vertical = a shared TEMPLATE + shared PLANES, verified by "
                  "the shared verifier, costed by the shared simulator + economic layer. The framework's full power on a "
                  "real vertical." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
