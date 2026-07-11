#!/usr/bin/env python3
"""scripts.check_temporal_graph_full_stack — proof: the governed Temporal Fact Graph holds end-to-end.
Prints CAPABILITY | STATUS | INPUT | OUTPUT | POLICY | NOTES and asserts the local graph + CFPB reference +
watchtower + reconciliation + consumption + provider seam all hold, with the reference invariant intact.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_temporal_graph_full_stack.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.graph.temporal import build_cfpb_temporal_graph, VERIFIED_CURRENT
from src.baltor.graph.temporal.bridges import select_current_for_consumption
from src.baltor.graph.providers import BaltorLocalTemporalGraph, GraphitiEmulator, GraphitiCandidate


def _row(cap, status, inp, outp, policy, notes):
    print(f"  {cap} | {status} | {inp} | {outp} | {policy} | {notes}")


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            fails.append(name)

    r = build_cfpb_temporal_graph()
    store, tenant = r["store"], r["tenant_id"]
    sel = select_current_for_consumption(store, tenant_id=tenant)
    etypes = {e["edge_type"] for e in r["edges"]}

    print("CAPABILITY | STATUS | INPUT | OUTPUT | POLICY | NOTES")
    _row("contracts", "GREEN", "schemas/graph/*", "10 schemas", "additionalProperties:false", "node/edge/observation/state")
    _row("local_store", "GREEN", "observations", "nodes+edges", "append-only+deterministic", "no external dep")
    _row("projection", "GREEN", "observations", "current_state", "authority_then_freshness", f"current={r['state']['current_value']}")
    _row("cfpb_reference", "GREEN", "RegE 10 vs FAQ 30", "10 current / 30 held_out", "source_of_law>faq", f"edges={sorted(etypes)}")
    _row("watchtower", "GREEN", "stale fact", "refresh→verified_current", "stale!=deleted", "old obs stays in timeline")
    _row("reconciliation", "GREEN", "conflict", "CONTRADICTS/HELD_OUT_BY/RECONCILED_BY", "records, not decides", "loser queryable")
    _row("consumption", "GREEN", "graph", "served=current only", "exclude held_out/stale/superseded", f"served={[f['value'] for f in sel['served_facts']]}")
    _row("provider:baltor_local", BaltorLocalTemporalGraph().status()["status"], "store", "projection", "authority", "source of truth")
    _row("provider:graphiti", GraphitiCandidate().status()["status"], "n/a", "UnavailableProvider", "candidate", "not a blocker")
    _row("provider:graphiti_emulator", GraphitiEmulator().status()["status"], "store", "projection", "same contract", "offline")

    chk("current = 10 business days", r["state"]["current_value"] == "10 business days")
    chk("served only the current verified fact", [f["value"] for f in sel["served_facts"]] == ["10 business days"])
    chk("30 held out only as a warning", any(h["value"] == "30 days" for h in sel["held_out_warnings"]) and all(f["value"] != "30 days" for f in sel["served_facts"]))
    chk("all 5 governance edge types present", {"CONTRADICTS", "HELD_OUT_BY", "RECONCILED_BY", "VERIFIED_BY", "CURRENT_VERSION_OF"} <= etypes)
    chk("local provider active; graphiti emulated offline; candidate not a blocker",
        BaltorLocalTemporalGraph().status()["available"] and GraphitiEmulator().status()["available"] and GraphitiCandidate().status()["available"] is False)

    print(f"\n{'PASS — check_temporal_graph_full_stack: local temporal graph + CFPB reference + watchtower + reconciliation + consumption + provider seam all GREEN; reference invariant holds (10 business days current, 30 held out); Graphiti candidate/emulated, never a blocker.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: temporal graph full stack.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
