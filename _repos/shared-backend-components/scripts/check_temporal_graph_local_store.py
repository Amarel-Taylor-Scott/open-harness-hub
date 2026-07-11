#!/usr/bin/env python3
"""scripts.check_temporal_graph_local_store — proof: the LOCAL deterministic temporal graph store works with
NO external dependency: append-only (held-out/superseded never deleted), content-addressed deterministic
node + edge ids (clock-independent), idempotent edges (rebuild does not duplicate), tenant-scoped reads
(cross-tenant private read refused), and the query surface (timeline/source-handle/contradiction/current).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_temporal_graph_local_store.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.graph.temporal import TemporalGraphStore, TenantScopeError, project_current, VERIFIED_CURRENT, HELD_OUT


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    s = TemporalGraphStore()
    n1 = s.add_observation(canonical_fact_key="k.deadline", tenant_id="global", scope="global_public",
                           subject="x", predicate="deadline", obj="10 business days", value_normalized="10 business days",
                           source_authority="source_of_law", source_handles=["ctx://law#1"], now="2026-01-01T00:00:00Z")
    n2 = s.add_observation(canonical_fact_key="k.deadline", tenant_id="global", scope="global_public",
                           subject="x", predicate="deadline", obj="30 days", value_normalized="30 days",
                           source_authority="official_faq", source_handles=["ctx://faq#1"], now="2026-01-01T00:00:00Z")
    chk("two distinct nodes (different value → different id)", n1.temporal_fact_id != n2.temporal_fact_id)

    # deterministic id: same logical observation in a fresh store with a DIFFERENT clock → same id
    s2 = TemporalGraphStore()
    n1b = s2.add_observation(canonical_fact_key="k.deadline", tenant_id="global", scope="global_public",
                             subject="x", predicate="deadline", obj="10 business days", value_normalized="10 business days",
                             source_authority="source_of_law", source_handles=["ctx://law#1"], now="2030-12-31T00:00:00Z")
    chk("node id is clock-independent (deterministic)", n1b.temporal_fact_id == n1.temporal_fact_id)

    e1 = s.add_edge(tenant_id="global", from_id=n2.temporal_fact_id, to_id=n1.temporal_fact_id, edge_type="CONTRADICTS", observed_at="2026-01-01T00:00:00Z")
    e1b = s.add_edge(tenant_id="global", from_id=n2.temporal_fact_id, to_id=n1.temporal_fact_id, edge_type="CONTRADICTS", observed_at="2026-01-01T00:00:00Z")
    chk("edge id deterministic + idempotent (no duplicate)", e1["edge_id"] == e1b["edge_id"] and len(s.edges("global", edge_type="CONTRADICTS")) == 1)
    try:
        s.add_edge(tenant_id="global", from_id=n1.temporal_fact_id, to_id=n2.temporal_fact_id, edge_type="BOGUS")
        chk("unknown edge_type rejected", False)
    except ValueError:
        chk("unknown edge_type rejected", True)

    # project + hold-out preserved (append-only: held-out node still present)
    project_current(s, canonical_fact_key="k.deadline", tenant_id="global", now="2026-01-01T00:00:00Z")
    chk("held-out node NOT deleted (append-only)", any(n["value_normalized"] == "30 days" for n in s.nodes("global")))
    chk("held-out queryable", any(n["value_normalized"] == "30 days" for n in s.held_out("global")))
    chk("current = 10 business days", [n["value_normalized"] for n in s.current_nodes("global")] == ["10 business days"])
    chk("timeline reconstructable (2 observations)", len(s.timeline("k.deadline", "global")) == 2)
    chk("source-handle query works", bool(s.by_source_handle("ctx://faq#1", "global")))

    # tenant scope: a tenant_private node is not readable cross-tenant
    s.add_observation(canonical_fact_key="k.private", tenant_id="acme", scope="tenant_private", subject="y",
                      predicate="sla", obj="5 days", value_normalized="5 days", source_authority="vendor_doc",
                      source_handles=["ctx://acme#1"], now="2026-01-01T00:00:00Z")
    priv = [n for n in s.nodes("acme") if n["canonical_fact_key"] == "k.private"]
    chk("tenant sees its own private node", bool(priv))
    chk("other tenant does NOT see private node", not any(n["canonical_fact_key"] == "k.private" for n in s.nodes("global")))
    try:
        s.get_node(priv[0]["temporal_fact_id"], tenant_id="global")
        chk("cross-tenant private get refused", False)
    except TenantScopeError:
        chk("cross-tenant private get refused", True)

    print(f"\n{'PASS — check_temporal_graph_local_store: local graph works with no external dep; append-only; deterministic+idempotent node/edge ids; tenant-scoped; timeline/source-handle/held-out/current queries.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: local temporal graph store.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
