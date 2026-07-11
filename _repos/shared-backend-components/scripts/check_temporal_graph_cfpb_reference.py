#!/usr/bin/env python3
"""scripts.check_temporal_graph_cfpb_reference — proof: the CFPB temporal graph makes Reg E "10 business days"
verified_current and holds out FAQ "30 days" (preserved, queryable), with CONTRADICTS / HELD_OUT_BY /
RECONCILED_BY / VERIFIED_BY / CURRENT_VERSION_OF edges, receipts, and source handles. The reference invariant
holds: 30 is NEVER served as the current fact; the loser remains in the graph.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_temporal_graph_cfpb_reference.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.graph.temporal import build_cfpb_temporal_graph, VERIFIED_CURRENT, HELD_OUT


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    r = build_cfpb_temporal_graph()
    store, state = r["store"], r["state"]
    chk("current value is '10 business days'", state["current_value"] == "10 business days", state["current_value"])
    chk("current state is verified_current", state["current_state"] == VERIFIED_CURRENT, state["current_state"])
    chk("FAQ '30 days' is held out (in state.held_out)", any(h["value"] == "30 days" for h in state["held_out"]))
    chk("current node carries a source handle", bool(r["current_node"]["source_handles"]))
    chk("held-out node carries a source handle (preserved)", bool(r["held_out_node"]["source_handles"]))
    chk("current node has a verification receipt", bool(r["current_node"]["verification_receipt_ids"]))
    chk("current node has a reconciliation receipt", bool(r["current_node"]["reconciliation_receipt_ids"]))

    etypes = {e["edge_type"] for e in r["edges"]}
    for et in ("CONTRADICTS", "HELD_OUT_BY", "RECONCILED_BY", "VERIFIED_BY", "CURRENT_VERSION_OF"):
        chk(f"edge {et} exists", et in etypes, str(sorted(etypes)))

    # the loser remains queryable (lossless), and is NOT the current served value
    held = store.held_out(r["tenant_id"])
    chk("held-out FAQ-30 remains queryable", any(n["value_normalized"] == "30 days" for n in held))
    cur = store.current_nodes(r["tenant_id"])
    chk("exactly one verified_current node = 10 business days",
        len(cur) == 1 and cur[0]["value_normalized"] == "10 business days", str([c["value_normalized"] for c in cur]))
    chk("30 days is NEVER verified_current", all(c["value_normalized"] != "30 days" for c in cur))

    # timeline + source-handle rehydration
    tl = store.timeline(r["fact_key"], r["tenant_id"])
    chk("timeline has both observations", len(tl) >= 2, str(len(tl)))
    chk("source handle rehydrates to the reg-e node",
        any(n["value_normalized"] == "10 business days" for n in store.by_source_handle("ctx://reg-e/1693f#1005.11", r["tenant_id"])))

    # determinism: rebuild → identical node/edge ids (idempotent, no duplicates)
    r2 = build_cfpb_temporal_graph()
    chk("rebuild is deterministic (same node id)", r2["current_node"]["temporal_fact_id"] == r["current_node"]["temporal_fact_id"])
    chk("rebuild does not duplicate edges", len(r2["edges"]) == len(r["edges"]), f"{len(r2['edges'])} vs {len(r['edges'])}")

    print(f"\n{'PASS — check_temporal_graph_cfpb_reference: Reg E 10 business days is verified_current; FAQ 30 days held out + preserved + queryable; CONTRADICTS/HELD_OUT_BY/RECONCILED_BY/VERIFIED_BY/CURRENT_VERSION_OF edges + receipts + source handles; deterministic rebuild.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: CFPB temporal graph reference.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
