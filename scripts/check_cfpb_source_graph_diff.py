#!/usr/bin/env python3
"""scripts.check_cfpb_source_graph_diff — proof: CFPB record builds a typed source graph and a content-hash
diff scopes change to exactly the artifact that changed (unchanged artifacts keep their content_hash).

CLI: python3 scripts/check_cfpb_source_graph_diff.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.pipeline_runtime.source_graph import build_cfpb_source_graph, diff_source_graph
from scripts.security.tenant_catalog import TenantPolicy

REC = {"complaint_id": "CFPB-1", "product": "Credit card", "issue": "Billing dispute",
       "company": "Acme Bank", "state": "CA", "date_received": "2026-01-02",
       "consumer_complaint_narrative": "I was charged twice. The company refused to refund me. This is unfair."}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    policy = TenantPolicy("acme")
    g0 = build_cfpb_source_graph(REC, policy)
    types = {a.artifact_type for a in g0.values()}
    check("source graph has source_record + source_field + sentence (+source_block)",
          {"source_record", "source_field", "sentence", "source_block"} <= types, str(types))
    check("structured fields each become a source_field",
          sum(1 for a in g0.values() if a.artifact_type == "source_field") >= 5)
    check("narrative split into multiple sentence artifacts",
          sum(1 for a in g0.values() if a.artifact_type == "sentence") == 3)

    # change ONE structured field
    rec2 = dict(REC, state="NY")
    g1 = build_cfpb_source_graph(rec2, policy)
    d = diff_source_graph(g0, g1)
    state_id = "CFPB-1:source_field:state"
    check("changing one structured field marks ONLY that field changed",
          d["changed"] == [state_id], str(d["changed"]))
    check("all other structured fields + sentences retain their content_hash",
          all(g0[a].content_hash == g1[a].content_hash for a in g0 if a != state_id))
    check("no spurious added/removed on a field-value edit", d["added"] == [] and d["removed"] == [])

    # change ONE narrative sentence (keep sentence count the same)
    rec3 = dict(REC, consumer_complaint_narrative="I was charged once. The company refused to refund me. This is unfair.")
    g2 = build_cfpb_source_graph(rec3, policy)
    d2 = diff_source_graph(g0, g2)
    s0 = "CFPB-1:sentence:consumer_complaint_narrative#s0"
    block = "CFPB-1:source_block:consumer_complaint_narrative"
    check("changing one sentence marks that sentence + its block changed (not structured fields)",
          set(d2["changed"]) == {s0, block}, str(d2["changed"]))
    check("structured-field facts' source artifacts unchanged by a narrative edit",
          g0["CFPB-1:source_field:state"].content_hash == g2["CFPB-1:source_field:state"].content_hash)

    print(f"\n{'PASS — check_cfpb_source_graph_diff: typed source graph built; content-hash diff scopes change to exactly the edited artifact; unchanged artifacts keep their hash.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: CFPB source graph + content-hash diff.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
