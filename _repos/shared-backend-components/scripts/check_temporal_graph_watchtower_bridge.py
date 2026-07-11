#!/usr/bin/env python3
"""scripts.check_temporal_graph_watchtower_bridge — proof: the temporal graph feeds fragile-fact logic. A
fragile fact can go STALE (no longer served, never replaced by a lower-authority claim), a verification task
REFRESHES it into a NEW observation that returns to verified_current, and the OLD stale observation remains
visible in the timeline (lossless).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_temporal_graph_watchtower_bridge.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.graph.temporal import build_cfpb_temporal_graph, project_current, VERIFIED_CURRENT, STALE
from src.baltor.graph.temporal.bridges import refresh_observation


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    r = build_cfpb_temporal_graph(now="2026-01-01T00:00:00Z")
    store, tenant, key = r["store"], r["tenant_id"], r["fact_key"]
    rege_id = r["current_node"]["temporal_fact_id"]

    # make the reg-e fact fragile with a freshness horizon, then project AFTER that horizon → stale
    store._nodes[rege_id].freshness = {"volatility_class": "fragile", "next_verify_at": "2026-03-01T00:00:00Z"}
    st = project_current(store, canonical_fact_key=key, tenant_id=tenant, now="2026-06-01T00:00:00Z")
    chk("stale top-authority fact yields NO verified_current", st["current_value"] == "" and st["current_state"] == STALE, str(st["current_state"]))
    chk("reg-e node is STALE", store._nodes[rege_id].current_state == STALE)
    chk("CRITICAL: FAQ-30 is NOT promoted when authority is stale",
        all(n["value_normalized"] != "30 days" for n in store.current_nodes(tenant)))
    timeline_before = len(store.timeline(key, tenant))

    # a verification task refreshes it → new observation, returns to verified_current
    out = refresh_observation(store, canonical_fact_key=key, tenant_id=tenant, scope="global_public",
                              subject="error_resolution", predicate="deadline", obj="10 business days",
                              value_normalized="10 business days", source_authority="source_of_law",
                              source_handles=["ctx://reg-e/1693f#1005.11"], unit="business_days",
                              now="2026-06-02T00:00:00Z", verify_receipt_id="verify-refresh-1", source_version="v2")
    chk("refresh returns to verified_current", out["state"]["current_state"] == VERIFIED_CURRENT and out["state"]["current_value"] == "10 business days")
    chk("refresh added a NEW observation (timeline grew)", out["timeline_len"] > timeline_before, f"{out['timeline_len']} vs {timeline_before}")
    chk("old stale observation remains in the timeline (lossless)", any(o["source_version"] == "v1" for o in store.timeline(key, tenant)))
    chk("refreshed node carries the verification receipt", "verify-refresh-1" in out["refreshed_node"]["verification_receipt_ids"])

    print(f"\n{'PASS — check_temporal_graph_watchtower_bridge: fragile fact → STALE (no current; FAQ never promoted) → verification refresh → new observation returns to verified_current; the old stale observation stays in the timeline (lossless).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: temporal graph watchtower bridge.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
