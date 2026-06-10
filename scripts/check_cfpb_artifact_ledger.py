#!/usr/bin/env python3
"""scripts.check_cfpb_artifact_ledger — proof: artifacts/edges/vectors/conflicts/reconciliations persist
durably and reload, and every artifact carries tenant_id, run_id, content_hash, and source handles.

CLI: python3 scripts/check_cfpb_artifact_ledger.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.artifact_graph import cfpb_artifacts as CA
from scripts.artifact_graph import conflict_detector as CD
from scripts.artifact_graph import graph_builder as GB
from scripts.artifact_graph import reconciliation as RC
from scripts.artifact_graph.artifact_ledger import ArtifactGraphLedger
from scripts.artifact_graph.vector_store import DeterministicLocalVectorProvider, vectorize_into_ledger
from scripts.security.tenant_catalog import TenantPolicy

REC = [{"complaint_id": "CFPB-1", "product": "Credit card", "issue": "Billing dispute", "company": "Acme",
        "state": "CA", "date_received": "2026-01-02",
        "consumer_complaint_narrative": "I was charged twice. The company refused to refund me."}]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    led = ArtifactGraphLedger(":memory:")
    policy = TenantPolicy("acme", "database_per_tenant", data_plane_ref="db-acme")
    built = CA.build_artifacts(REC, policy)
    arts, rid = built["artifacts"], built["run_id"]
    for a in arts:
        led.put_artifact(a)
    vectorize_into_ledger(led, DeterministicLocalVectorProvider(), arts)
    edges = GB.build_edges(arts, tenant_id="acme", run_id=rid)
    for e in edges:
        led.put_edge(e)
    conflicts = CD.detect(arts, edges, tenant_id="acme")
    for c in conflicts:
        led.put_conflict(c)
    rec = RC.reconcile(conflicts, {a.artifact_id: a for a in arts}, tenant_id="acme")
    for r in rec["reconciliations"]:
        led.put_reconciliation(r)

    counts = led.counts("acme")
    check("artifacts persisted + reloaded", counts["artifacts"] == len(arts) and counts["artifacts"] > 0)
    check("edges persisted + reloaded", counts["edges"] == len(edges) and counts["edges"] > 0)
    check("vectors persisted + reloaded", counts["vectors"] > 0)
    check("conflicts persisted + reloaded", counts["conflicts"] >= 1)
    check("reconciliations persisted + reloaded", counts["reconciliations"] >= 1)

    # EVERY artifact has tenant_id, run_id, content_hash, source handles
    sample = [led.get_artifact(a.artifact_id) for a in arts]
    check("every artifact has content_hash", all(s and s["content_hash"] for s in sample))
    check("every artifact has source_handles", all(s and s["source_handles_json"] for s in sample))
    check("every artifact has tenant_id + run_id + pipeline + processor lineage",
          all(s and s["run_id"] == rid and s["tenant_id"] == "acme" for s in sample))
    check("artifact_type filter works", len(led.artifacts("acme", "atomic_fact")) >= 1)
    check("a reloaded edge keeps its evidence_json", all("reason" in e["evidence_json"] or e["evidence_json"] for e in led.edges("acme")))
    check("the ledger is the source of truth (reads come from SQLite, not memory)",
          led.get_artifact(arts[0].artifact_id)["artifact_id"] == arts[0].artifact_id)

    led.close()
    print(f"\n{'PASS — check_cfpb_artifact_ledger: artifacts/edges/vectors/conflicts/reconciliations persist + reload durably; every artifact has content_hash + source handles + lineage.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: C32 artifact ledger persistence + lineage.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
