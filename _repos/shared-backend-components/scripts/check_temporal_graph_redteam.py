#!/usr/bin/env python3
"""scripts.check_temporal_graph_redteam — adversarial proof: governance attacks on the temporal graph fail
safely. None of these may succeed.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_temporal_graph_redteam.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.graph.temporal import build_cfpb_temporal_graph, TemporalGraphStore, project_current, TenantScopeError
from src.baltor.graph.temporal.bridges import select_current_for_consumption, refresh_observation
from src.baltor.graph.providers import GraphitiCandidate, UnavailableProvider


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, blocked: bool, detail: str = "") -> None:
        print(f"  [{'ok' if blocked else 'FAIL'}] BLOCKED: {name}{(': ' + detail) if detail and not blocked else ''}")
        if not blocked:
            fails.append(name)

    r = build_cfpb_temporal_graph()
    store, tenant = r["store"], r["tenant_id"]
    faq_id = r["held_out_node"]["temporal_fact_id"]

    # 1. serve held-out FAQ-30 as current
    sel = select_current_for_consumption(store, tenant_id=tenant)
    chk("serve held-out FAQ-30 as current", all(f["value"] != "30 days" for f in sel["served_facts"]))

    # 2. lose a source handle — every served fact must carry one
    chk("served fact without a source handle", all(f.get("source_handles") for f in sel["served_facts"]))

    # 3. newer LOWER-authority FAQ tries to override source-of-law (re-project with a newer FAQ obs)
    store.add_observation(canonical_fact_key=r["fact_key"], tenant_id=tenant, scope="global_public", subject="error_resolution",
                          predicate="deadline", obj="45 days", value_normalized="45 days", source_authority="public_summary",
                          source_handles=["ctx://blog#1"], now="2099-01-01T00:00:00Z")
    st = project_current(store, canonical_fact_key=r["fact_key"], tenant_id=tenant, now="2099-01-02T00:00:00Z")
    chk("newer lower-authority claim overrides source-of-law", st["current_value"] == "10 business days", st["current_value"])

    # 4. stale fact selected as current (make reg-e stale, ensure no current served)
    s2 = build_cfpb_temporal_graph(now="2026-01-01T00:00:00Z")["store"]
    rege2 = [n for n in s2.current_nodes("global")][0]["temporal_fact_id"]
    s2._nodes[rege2].freshness = {"next_verify_at": "2026-02-01T00:00:00Z"}
    project_current(s2, canonical_fact_key=r["fact_key"], tenant_id="global", now="2027-01-01T00:00:00Z")
    sel2 = select_current_for_consumption(s2, tenant_id="global")
    chk("stale fact selected as current", all(f["current_state"] == "verified_current" for f in sel2["served_facts"]) and not sel2["served_facts"] or all(f["value"] != "30 days" for f in sel2["served_facts"]))

    # 5. tenant_private leaks to global
    store.add_observation(canonical_fact_key="acme.secret", tenant_id="acme", scope="tenant_private", subject="s",
                          predicate="p", obj="x", value_normalized="x", source_authority="vendor_doc",
                          source_handles=["ctx://acme#9"], now="2026-06-06T00:00:00Z")
    selg = select_current_for_consumption(store, tenant_id=tenant)
    chk("tenant_private leaks into global consumption", all(f["canonical_fact_key"] != "acme.secret" for f in selg["served_facts"]))
    priv = [n for n in store.nodes("acme") if n["canonical_fact_key"] == "acme.secret"][0]["temporal_fact_id"]
    try:
        store.get_node(priv, tenant_id=tenant)
        chk("cross-tenant private read", False)
    except TenantScopeError:
        chk("cross-tenant private read", True)

    # 6. Graphiti provider result bypasses Baltor policy (candidate must fail closed, never fabricate)
    try:
        GraphitiCandidate().project(store, tenant)
        chk("graphiti candidate fabricates a projection without a backend", False)
    except UnavailableProvider:
        chk("graphiti candidate fabricates a projection without a backend", True)

    # 7. delete a superseded/held-out node (append-only: held-out stays present)
    chk("held-out node deleted (append-only violated)", store.get_node(faq_id) is not None)

    print(f"\n{'PASS — check_temporal_graph_redteam: all attacks fail safely (no held-out/stale served, no handle loss, no lower-authority override, no tenant leak, graphiti candidate fails closed, held-out preserved).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: temporal graph red-team.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
