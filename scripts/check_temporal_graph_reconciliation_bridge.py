#!/usr/bin/env python3
"""scripts.check_temporal_graph_reconciliation_bridge — proof: the graph RECORDS reconciliation (it does not
replace it). A conflict becomes CONTRADICTS; the decision becomes RECONCILED_BY + HELD_OUT_BY edges carrying
the receipt; the losing claim stays queryable (lossless); the winner is verified_current.

CLI: PYTHONPATH=. python3 scripts/check_temporal_graph_reconciliation_bridge.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.graph.temporal import TemporalGraphStore, VERIFIED_CURRENT, HELD_OUT
from src.baltor.graph.temporal.bridges import record_reconciliation


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    s = TemporalGraphStore()
    win = s.add_observation(canonical_fact_key="k.deadline", tenant_id="global", scope="global_public", subject="x",
                            predicate="deadline", obj="10 business days", value_normalized="10 business days",
                            source_authority="source_of_law", source_handles=["ctx://law#1"], now="2026-01-01T00:00:00Z")
    los = s.add_observation(canonical_fact_key="k.deadline", tenant_id="global", scope="global_public", subject="x",
                            predicate="deadline", obj="30 days", value_normalized="30 days",
                            source_authority="official_faq", source_handles=["ctx://faq#1"], now="2026-01-01T00:00:00Z")
    edges = record_reconciliation(s, winner_id=win.temporal_fact_id, loser_id=los.temporal_fact_id,
                                  tenant_id="global", recon_receipt_id="recon-1", now="2026-01-02T00:00:00Z")
    ets = {e["edge_type"] for e in edges}
    for et in ("CONTRADICTS", "HELD_OUT_BY", "RECONCILED_BY"):
        chk(f"{et} edge written", et in ets)
    chk("every recorded edge carries the reconciliation receipt", all(e["receipt_id"] == "recon-1" for e in edges))
    chk("winner is verified_current", s.get_node(win.temporal_fact_id)["current_state"] == VERIFIED_CURRENT)
    chk("loser is held_out", s.get_node(los.temporal_fact_id)["current_state"] == HELD_OUT)
    chk("losing claim remains QUERYABLE (lossless)", any(n["value_normalized"] == "30 days" for n in s.held_out("global")))
    chk("loser carries the reconciliation receipt", "recon-1" in s.get_node(los.temporal_fact_id)["reconciliation_receipt_ids"])
    # idempotent: recording again does not duplicate edges
    e2 = record_reconciliation(s, winner_id=win.temporal_fact_id, loser_id=los.temporal_fact_id,
                               tenant_id="global", recon_receipt_id="recon-1", now="2026-01-02T00:00:00Z")
    chk("re-record is idempotent (same edge ids)", {e["edge_id"] for e in e2} == {e["edge_id"] for e in edges})

    print(f"\n{'PASS — check_temporal_graph_reconciliation_bridge: graph records reconciliation as CONTRADICTS/HELD_OUT_BY/RECONCILED_BY edges + receipts; winner verified_current, loser held_out but queryable (lossless); idempotent.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: temporal graph reconciliation bridge.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
