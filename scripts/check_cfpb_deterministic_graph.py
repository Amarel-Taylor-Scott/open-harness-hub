#!/usr/bin/env python3
"""scripts.check_cfpb_deterministic_graph — proof: the deterministic graph is byte-identical across runs,
contains the required edge layers (parent/child, source→fact, entity, conclusion support), and every edge
carries evidence_json.

CLI: python3 scripts/check_cfpb_deterministic_graph.py --self-test
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from scripts.artifact_graph import cfpb_artifacts as CA
from scripts.artifact_graph import graph_builder as GB
from scripts.security.tenant_catalog import TenantPolicy

REC = [{"complaint_id": "CFPB-1", "product": "Credit card", "issue": "Billing dispute", "company": "Acme",
        "state": "CA", "date_received": "2026-01-02",
        "consumer_complaint_narrative": "I was charged twice. Acme refused to refund me."},
       {"complaint_id": "CFPB-2", "product": "Credit card", "issue": "Billing dispute", "company": "Acme",
        "state": "NY", "date_received": "2026-01-05",
        "consumer_complaint_narrative": "My statement is wrong. Nobody will fix it."}]


def _serialize(edges) -> str:
    return json.dumps([asdict(e) for e in edges], sort_keys=True)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    policy = TenantPolicy("acme")
    arts = CA.build_artifacts(REC, policy)["artifacts"]
    rid = CA.run_id_for(REC, "acme")

    e1 = GB.build_edges(arts, tenant_id="acme", run_id=rid)
    e2 = GB.build_edges(CA.build_artifacts(REC, policy)["artifacts"], tenant_id="acme", run_id=rid)
    check("graph edge set is BYTE-IDENTICAL across runs", _serialize(e1) == _serialize(e2), f"{len(e1)} vs {len(e2)} edges")
    check("edge_ids are deterministic (from tenant+from+type+to+run_id)",
          {e.edge_id for e in e1} == {e.edge_id for e in e2})

    types = {e.edge_type for e in e1}
    required = {"CONTAINS", "HAS_FIELD", "HAS_SENTENCE", "YIELDS_FACT", "YIELDS_ALLEGATION", "MENTIONS",
                "SAME_COMPLAINT_AS", "SUPPORTED_BY"}
    check("graph contains all required deterministic edge layers", required <= types, str(sorted(types)))
    check("cross-complaint SAME_COMPANY_AS link exists (Acme in both complaints)", "SAME_COMPANY_AS" in types)
    check("every edge has evidence_json", all(e.evidence_json for e in e1))
    check("every edge is edge_source=deterministic with confidence", all(e.edge_source == "deterministic" and e.confidence == 1.0 for e in e1))
    check("parent/child layer present (CONTAINS/HAS_FIELD)", {"CONTAINS", "HAS_FIELD"} <= types)
    check("source→fact layer present (YIELDS_FACT)", "YIELDS_FACT" in types)
    check("entity layer present (MENTIONS)", "MENTIONS" in types)

    print(f"\n{'PASS — check_cfpb_deterministic_graph: deterministic edges are byte-identical across runs, cover all required layers, and each carries evidence.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: C32 deterministic graph reproducibility + coverage.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
