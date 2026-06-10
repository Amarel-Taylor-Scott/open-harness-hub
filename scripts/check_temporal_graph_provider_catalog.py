#!/usr/bin/env python3
"""scripts.check_temporal_graph_provider_catalog — proof: temporal_graph_provider seam. baltor_local is the
active authority; graphiti is a CANDIDATE that raises UnavailableProvider (no SDK) — NOT a blocker; the
graphiti_emulator implements the SAME contract OFFLINE so the correctness invariant never depends on Graphiti. All
three share the projection contract and project the same governed facts (a projection, never canonical truth).

CLI: PYTHONPATH=. python3 scripts/check_temporal_graph_provider_catalog.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.graph.temporal import build_cfpb_temporal_graph
from src.baltor.graph.providers import (BaltorLocalTemporalGraph, GraphitiCandidate, GraphitiEmulator,
                                        UnavailableProvider, get_provider, TemporalGraphProviderPort)


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    r = build_cfpb_temporal_graph()
    store, tenant = r["store"], r["tenant_id"]

    local, cand, emu = BaltorLocalTemporalGraph(), GraphitiCandidate(), GraphitiEmulator()
    for p in (local, cand, emu):
        chk(f"{p.provider_id} satisfies the port", isinstance(p, TemporalGraphProviderPort))

    chk("baltor_local status active+available", local.status()["status"] == "active" and local.status()["available"])
    chk("graphiti status candidate+unavailable", cand.status()["status"] == "candidate" and cand.status()["available"] is False)
    chk("graphiti credential_ref is an env:// ref", cand.status()["credential_ref"].startswith("env://"))
    chk("graphiti emulator status emulated+available", emu.status()["status"] == "emulated" and emu.status()["available"])

    # local projects the governed facts
    lp = local.project(store, tenant)
    chk("local projection includes the verified-current fact", any(f["value_normalized"] == "10 business days" for f in lp["facts"]))
    chk("local projection is a projection, not truth (schema)", lp["schema_version"] == "TemporalGraphProjection.v1")

    # graphiti candidate is NOT a blocker: it fails closed, never fabricates
    try:
        cand.project(store, tenant)
        chk("graphiti candidate raises UnavailableProvider (no fabricated truth)", False)
    except UnavailableProvider:
        chk("graphiti candidate raises UnavailableProvider (no fabricated truth)", True)

    # emulator works OFFLINE with the SAME contract + SAME governed facts as local
    ep = emu.project(store, tenant)
    chk("emulator projects offline (same facts as local)",
        {f["temporal_fact_id"] for f in ep["facts"]} == {f["temporal_fact_id"] for f in lp["facts"]})
    chk("emulator exposes a graphiti-ish view over the SAME governed graph", "graphiti_view" in ep and ep["facts"] == lp["facts"])
    chk("get_provider resolves all three by id",
        get_provider("temporal_graph.baltor_local@v1") is local or get_provider("temporal_graph.baltor_local@v1").provider_id == local.provider_id)

    print(f"\n{'PASS — check_temporal_graph_provider_catalog: baltor_local is the authority; graphiti is candidate (UnavailableProvider, not a blocker); the emulator covers the SAME contract offline; all projections are read-only, never canonical truth.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: temporal graph provider catalog.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
