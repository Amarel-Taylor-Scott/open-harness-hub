#!/usr/bin/env python3
"""scripts.check_storage_model_flexible — proof: the canonical artifact ledger is a flexible long/narrow
store (many artifact types, NO per-type wide columns, NO migration), JSON payload + content-addressed
object-store payload_ref both work, and projections are disposable/rebuildable from the canonical ledger.

CLI: python3 scripts/check_storage_model_flexible.py --self-test
"""
from __future__ import annotations

import argparse
import shutil
import tempfile

from scripts.artifact_graph import cfpb_artifacts as CA
from scripts.artifact_graph.artifact_ledger import ArtifactGraphLedger
from scripts.artifact_graph.vector_store import DeterministicLocalVectorProvider, vectorize_into_ledger
from scripts.runtime.object_store import LocalObjectStore
from scripts.runtime.projections import build_fact_projection, build_type_projection, build_vector_projection
from scripts.security.tenant_catalog import TenantPolicy

REC = [{"complaint_id": "CFPB-1", "product": "Credit card", "issue": "Billing dispute", "company": "Acme",
        "state": "CA", "date_received": "2026-01-02",
        "consumer_complaint_narrative": "I was charged twice. The company refused to refund me."}]

#: type-specific column names that would indicate a fragile WIDE table (must NOT appear)
WIDE_SMELLS = ("complaint_product", "sentence_text", "emotion_score", "conclusion_text", "vector_1", "vector_2")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    led = ArtifactGraphLedger(":memory:")
    arts = CA.build_artifacts(REC, TenantPolicy("acme"))["artifacts"]
    for a in arts:
        led.put_artifact(a)
    vectorize_into_ledger(led, DeterministicLocalVectorProvider(), arts)

    bt = led.counts_by_type("acme")
    check("many DISTINCT artifact types stored under ONE schema (no migration)", len(bt) >= 8, str(sorted(bt)))

    cols = [d[1] for d in led.conn.execute("PRAGMA table_info(artifacts)").fetchall()]
    check("canonical table is long/narrow — NO per-type wide columns",
          not any(s in cols for s in WIDE_SMELLS) and "payload_json" in cols, str(cols))
    check("canonical table carries lineage columns generically",
          {"artifact_type", "content_hash", "pipeline_id", "processor_id", "run_id", "payload_json"} <= set(cols))

    sample = led.get_artifact(arts[0].artifact_id)
    check("payload_json round-trips as structured JSON", isinstance(sample["payload_json"], dict))

    # object store: large payload by content-addressed ref (the payload_ref pattern)
    tmp = tempfile.mkdtemp(prefix="objstore-")
    store = LocalObjectStore(tmp)
    big = {"raw_model_response": "x" * 5000, "note": "too big for the dashboard / artifact JSON"}
    meta = store.put("acme", big)
    check("object store returns a content-addressed payload_ref + content_hash + size",
          meta["payload_ref"].startswith("object://acme/") and meta["content_hash"] and meta["size_bytes"] > 5000)
    import json as _j
    check("object payload round-trips by ref", _j.loads(store.get(meta["payload_ref"])) == big)
    check("same content → same ref (content-addressed, idempotent)", store.put("acme", big)["payload_ref"] == meta["payload_ref"])

    # projections are rebuildable from the canonical ledger
    fp1 = build_fact_projection(led, "acme")
    fp2 = build_fact_projection(led, "acme")  # rebuild → identical
    check("fact projection is rebuildable + deterministic from the canonical ledger", fp1 == fp2 and len(fp1) > 0)
    check("type + vector projections rebuild from canonical ledger",
          build_type_projection(led, "acme") == bt and len(build_vector_projection(led, "acme")) > 0)

    led.close()
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'PASS — check_storage_model_flexible: flexible long/narrow canonical ledger (many types, no wide columns, no migration) + JSON payload + content-addressed object_store ref + rebuildable projections.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: hybrid flexible storage model.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
