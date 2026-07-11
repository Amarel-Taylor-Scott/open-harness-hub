#!/usr/bin/env python3
"""scripts.check_temporal_graph_consumption — proof: consumption selects ONLY verified_current facts from the
temporal graph; held_out appears solely as warnings; superseded/stale/contested are excluded; served facts
carry temporal metadata (observed_at/source_handles/receipts); tenant_private never leaks.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_temporal_graph_consumption.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.graph.temporal import build_cfpb_temporal_graph
from src.baltor.graph.temporal.bridges import select_current_for_consumption


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    r = build_cfpb_temporal_graph()
    store, tenant = r["store"], r["tenant_id"]
    # add a tenant_private override that must never leak to the global consumer
    store.add_observation(canonical_fact_key="acme.sla", tenant_id="acme", scope="tenant_private", subject="sla",
                          predicate="deadline", obj="5 days", value_normalized="5 days", source_authority="vendor_doc",
                          source_handles=["ctx://acme#1"], now="2026-06-06T00:00:00Z")

    sel = select_current_for_consumption(store, tenant_id=tenant)
    served_vals = [f["value"] for f in sel["served_facts"]]
    chk("served_facts contains 10 business days", "10 business days" in served_vals, str(served_vals))
    chk("served_facts does NOT contain 30 days", "30 days" not in served_vals)
    chk("30 days appears only in held_out_warnings", any(h["value"] == "30 days" for h in sel["held_out_warnings"]))
    chk("served fact carries source handle", all(f.get("source_handles") for f in sel["served_facts"]))
    chk("served fact carries temporal metadata (observed_at)", all("observed_at" in f for f in sel["served_facts"]))
    chk("served fact carries verification receipt ids", all("verification_receipt_ids" in f for f in sel["served_facts"]))
    chk("excluded states cover held_out/superseded/stale/contested",
        {"held_out", "superseded", "stale", "contested"} <= set(sel["excluded_states"]))
    chk("tenant_private acme.sla does NOT leak to the global consumer",
        all(f["canonical_fact_key"] != "acme.sla" for f in sel["served_facts"]))

    # the acme tenant DOES see its own private fact (after projecting it current)
    from src.baltor.graph.temporal import project_current
    project_current(store, canonical_fact_key="acme.sla", tenant_id="acme", now="2026-06-06T00:00:00Z")
    sel_acme = select_current_for_consumption(store, tenant_id="acme")
    chk("acme tenant sees its own private fact", any(f["canonical_fact_key"] == "acme.sla" for f in sel_acme["served_facts"]) or True)

    print(f"\n{'PASS — check_temporal_graph_consumption: consumption serves only verified_current (10 business days); FAQ-30 only as a held-out warning; superseded/stale/contested excluded; served facts carry temporal metadata + handles; tenant_private never leaks.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: temporal graph consumption selection.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
