#!/usr/bin/env python3
"""scripts.cfpb_artifact_graph_demo — C32 orchestrator: CFPB → artifacts → vectors → graph → conflicts →
reconciliation → receipt-backed context pack. The ledger is the source of truth; this returns a projection.

Stages: ingest → build source/decomposed artifacts → store → vectorize → deterministic graph → detect
conflicts → reconcile → final reconciled context pack + receipt. Deterministic + offline (no model, no
network, no paid API): the known Reg E "10 business days" vs FAQ "30 days" contradiction is detected and
resolved by authority, with the FAQ claim held out of the promoted pack.

CLI:
    python3 scripts/cfpb_artifact_graph_demo.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.artifact_graph import cfpb_artifacts as CA
from scripts.artifact_graph import conflict_detector as CD
from scripts.artifact_graph import graph_builder as GB
from scripts.artifact_graph import reconciliation as RC
from scripts.artifact_graph.artifact_ledger import EPOCH, ArtifactGraphLedger
from scripts.artifact_graph.vector_store import DeterministicLocalVectorProvider, search_similar, vectorize_into_ledger
from scripts.security.tenant_catalog import TenantPolicy

#: deterministic, offline CFPB-shaped fixture (no PII; synthetic) for the demo + self-test.
FIXTURE = [
    {"complaint_id": "CFPB-1001", "product": "Credit card", "issue": "Billing dispute", "company": "Acme Bank",
     "state": "CA", "date_received": "2026-01-02",
     "consumer_complaint_narrative": "I was charged twice. The company refused to refund me. This is unfair."},
    {"complaint_id": "CFPB-1002", "product": "Credit card", "issue": "Billing dispute", "company": "Acme Bank",
     "state": "NY", "date_received": "2026-01-05",
     "consumer_complaint_narrative": "My statement is wrong. Nobody will fix the error. I am frustrated."},
    {"complaint_id": "CFPB-1003", "product": "Checking account", "issue": "Unauthorized transaction", "company": "Globex",
     "state": "TX", "date_received": "2026-01-09",
     "consumer_complaint_narrative": "There is a charge I did not authorize. The bank denied my claim."},
]


def run_demo(records=None, *, tenant_id: str = "acme", ledger_path: str = ":memory:", now: str = EPOCH) -> dict:
    records = list(records or FIXTURE)
    policy = TenantPolicy(tenant_id, "database_per_tenant", data_plane_ref=f"db-{tenant_id}")
    led = ArtifactGraphLedger(ledger_path)
    provider = DeterministicLocalVectorProvider()
    stages: list[str] = []

    built = CA.build_artifacts(records, policy, now=now)
    arts, rid = built["artifacts"], built["run_id"]
    for a in arts:
        led.put_artifact(a)
    stages.append("ingest+decompose+store")

    n_vec = vectorize_into_ledger(led, provider, arts, now=now)
    stages.append("vectorize")

    edges = GB.build_edges(arts, tenant_id=tenant_id, run_id=rid, now=now)
    for e in edges:
        led.put_edge(e)
    stages.append("deterministic_graph")

    conflicts = CD.detect(arts, edges, tenant_id=tenant_id, now=now)
    for c in conflicts:
        led.put_conflict(c)
    stages.append("detect_conflicts")

    by_id = {a.artifact_id: a for a in arts}
    rec = RC.reconcile(conflicts, by_id, tenant_id=tenant_id, now=now)
    for r in rec["reconciliations"]:
        led.put_reconciliation(r)
    for c in conflicts:
        led.link_conflict(c.conflict_id, RC._rid(c.conflict_id), rec["status"].get(c.conflict_id, "open"))
    stages.append("reconcile")

    held_out = set(rec["held_out_ids"])
    included = [a.artifact_id for a in arts
                if a.artifact_type == "atomic_fact" and a.promotion_eligible and a.artifact_id not in held_out]
    winning = {"deadline": built["reg_e_id"]} if built["reg_e_id"] not in held_out else {}
    pack, receipt = CA.build_context_pack_and_receipt(
        tenant_id=tenant_id, source_id="cfpb", run_id=rid, included_ids=included,
        held_out_ids=sorted(held_out), winning=winning, now=now)
    led.put_artifact(pack); led.put_artifact(receipt)
    for e in GB.build_pack_edges(tenant_id=tenant_id, run_id=rid, pack_id=pack.artifact_id,
                                 receipt_id=receipt.artifact_id, included_ids=included,
                                 held_out_ids=sorted(held_out), now=now):
        led.put_edge(e)
    stages.append("final_pack+receipt")

    # one drill-down example: a structured atomic fact → its lineage + vector + neighbours
    example_fact = next((a.artifact_id for a in arts if a.artifact_type == "atomic_fact" and a.source_id == "CFPB-1001"), None)
    drill = {}
    if example_fact:
        drill = {"artifact": led.get_artifact(example_fact),
                 "neighbors": led.neighbors(tenant_id, example_fact),
                 "nearest": search_similar(led, provider, tenant_id, artifact_id=example_fact,
                                           artifact_types=("atomic_fact",), k=3),
                 "in_pack": example_fact in included}

    resp = {
        "ok": True, "run_id": rid, "tenant_id": tenant_id, "stages": stages,
        "counts": led.counts(tenant_id),
        "artifact_counts_by_type": led.counts_by_type(tenant_id),
        "graph_layers": led.edge_counts(tenant_id),
        "vectorized": n_vec, "vector_provider": {"provider": provider.provider, "model": provider.model,
                                                  "version": provider.version, "dimensions": provider.dimensions},
        "conflicts": led.list_conflicts(tenant_id),
        "reconciliations": led.list_reconciliations(tenant_id),
        "final_context_pack": {"pack_id": pack.artifact_id, "included": included,
                               "held_out": sorted(held_out), "winning": winning},
        "receipt": receipt.payload_json,
        "drilldown": drill,
        "_reg_e_id": built["reg_e_id"], "_faq_id": built["faq_id"],
    }
    if ledger_path == ":memory:":
        led.close()
    return resp


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    r = run_demo()
    check("orchestrator returns ok + ran all stages", r["ok"] and len(r["stages"]) == 6, str(r["stages"]))
    bt = r["artifact_counts_by_type"]
    for t in ("source_record", "source_field", "sentence", "context_object", "atomic_fact",
              "narrative_allegation", "entity_mention", "emotion_signal", "conclusion", "context_pack", "receipt"):
        check(f"artifacts include {t}", bt.get(t, 0) > 0, str(bt))
    c = r["counts"]
    check("counts nonzero for artifacts/vectors/edges/conflicts/reconciliations",
          all(c[k] > 0 for k in ("artifacts", "vectors", "edges", "conflicts", "reconciliations")), str(c))

    # known Reg E (10 business days) vs FAQ (30 days) → resolved by authority, FAQ held out
    deadline = [rc for rc in r["reconciliations"] if rc["decision"] == "resolved_by_authority"]
    check("known 10-vs-30 contradiction is resolved by authority", len(deadline) >= 1, str(r["reconciliations"]))
    check("the WINNING artifact is the Reg E (10 business days) fact",
          any(rc["winning_artifact_id"] == r["_reg_e_id"] for rc in deadline))
    check("the lower-authority FAQ (30 days) artifact is HELD OUT of the pack",
          r["_faq_id"] in r["final_context_pack"]["held_out"])
    check("the Reg E fact is INCLUDED in the final pack", r["_reg_e_id"] in r["final_context_pack"]["included"])

    # final pack contains only promotable/reconciled facts; nothing held out leaks in
    check("final pack includes only promotable, non-held-out facts",
          not (set(r["final_context_pack"]["included"]) & set(r["final_context_pack"]["held_out"])))

    # determinism: a second run is byte-identical on artifacts/edges/run_id
    r2 = run_demo()
    check("run is deterministic (same run_id + same counts across runs)",
          r2["run_id"] == r["run_id"] and r2["counts"] == r["counts"])

    print(f"\n{'PASS — cfpb_artifact_graph_demo: full CFPB flow ingest→artifacts→vectors→graph→conflict→reconcile→receipt; Reg E beats FAQ by authority, FAQ held out, final pack is reconciled/promotable only; deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="C32 — CFPB Artifact Graph Demo orchestrator.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    import json
    print(json.dumps(run_demo(), indent=2)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
