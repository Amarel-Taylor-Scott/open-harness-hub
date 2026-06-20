#!/usr/bin/env python3
"""scripts.check_pipeline_runtime — proof: registry + versioned runs + swap + reprocessing + seam.

In-process (fast, deterministic) proof of Pipeline Runtime v1:
  * manifests discover + validate (active steps reference registered processors; inputs/outputs declared)
  * cfpb_structured_ingest@v1 runs through the GENERIC runner → atomic facts, held-out allegations,
    gates pass, receipt counts match, content-addressed artifacts
  * v1 and v2 run side-by-side (distinct run_ids, distinct output hashes, both readable; v2 lineage shows
    package.context_pack@v2 = processor swap by manifest)
  * reprocessing: same input+version = duplicate (no-op); changed input OR changed pipeline version = NEW run
  * unstructured_pdf_docling@v0 is discoverable + experimental; running it returns a clear
    unavailable_processor error recorded in the run ledger (not a crash)

CLI:
    python3 scripts/check_pipeline_runtime.py --self-test
"""
from __future__ import annotations

import argparse
import tempfile
import shutil

from scripts.durable_store import DurableStore
from scripts.pipeline_runtime.processors import default_registry
from scripts.pipeline_runtime.runner import run_pipeline
from scripts.pipeline_runtime.specs import discover, validate
from scripts.pipeline_runtime.store import PipelineLedger


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    reg = default_registry()
    specs = discover()

    # ── registry + manifests ──
    check("cfpb_structured_ingest@v1 discovered", "cfpb_structured_ingest@v1" in specs)
    check("cfpb_structured_ingest@v2 discovered", "cfpb_structured_ingest@v2" in specs)
    check("unstructured_pdf_docling@v0 discovered as experimental",
          specs.get("unstructured_pdf_docling@v0") and specs["unstructured_pdf_docling@v0"].status == "experimental")
    v1 = specs["cfpb_structured_ingest@v1"]
    check("v1 validates clean against the registry", validate(v1, registry=reg) == [], str(validate(v1, registry=reg)))
    check("every active step references a registered processor", all(reg.has(s.processor_ref) for s in v1.steps))
    check("every step declares output_artifact_types", all(s.output_artifact_types for s in v1.steps))
    check("active pipeline has an idempotency_key_template", bool(v1.idempotency_key_template))

    tmp = tempfile.mkdtemp(prefix="pipe-rt-")
    store = DurableStore(tmp + "/d.db")
    ledger = PipelineLedger(store)
    run_input = {"fixture": True, "limit": 5, "source_id": "cfpb-fixture"}

    # ── run v1 through the GENERIC runner ──
    r1 = run_pipeline(v1, tenant_id="acme", run_input=run_input, ledger=ledger, registry=reg)
    check("v1 run reaches done", r1["status"] == "done", str(r1))
    rec1 = ledger.get_run(r1["run_id"])
    check("run ledger records pipeline + version + tenant", rec1["pipeline_version"] == "v1" and rec1["tenant_id"] == "acme")
    check("all 4 steps recorded done", len(rec1["steps"]) == 4 and all(s["status"] == "done" for s in rec1["steps"]))
    facts_art = ledger.get_artifact(r1["artifact_ids"]["AtomicFactSet.v1"])
    check("AtomicFactSet artifact content-addressed (>0 facts, #field handles)",
          facts_art["content_hash"] and facts_art["payload"]["count"] > 0
          and all("#" in f["source_handle"] for f in facts_art["payload"]["facts"]))
    held = ledger.get_artifact(r1["artifact_ids"]["HeldOutAllegationSet.v1"])
    check("held-out allegations NOT promotion-eligible", all(not a["promotion_eligible"] for a in held["payload"]["allegations"]))
    check("all gates passed", r1["failed_gates"] == [], str(r1["gates"]))
    receipt = ledger.get_artifact(r1["artifact_ids"]["Receipt.v1"])["payload"]
    check("receipt facts_served matches verified fact count", receipt["facts_served"] == facts_art["payload"]["count"])

    # ── reprocessing semantics ──
    again = run_pipeline(v1, tenant_id="acme", run_input=run_input, ledger=ledger, registry=reg)
    check("re-run same input+version = DUPLICATE (no-op)", again["duplicate"] and again["run_id"] == r1["run_id"])
    changed_input = run_pipeline(v1, tenant_id="acme", run_input={**run_input, "limit": 3}, ledger=ledger, registry=reg)
    check("changed INPUT = new run (reprocessing)", not changed_input["duplicate"] and changed_input["run_id"] != r1["run_id"])

    # ── versions side-by-side + processor swap by manifest ──
    v2 = specs["cfpb_structured_ingest@v2"]
    r2 = run_pipeline(v2, tenant_id="acme", run_input=run_input, ledger=ledger, registry=reg)
    check("v2 run reaches done", r2["status"] == "done", str(r2))
    check("changed pipeline VERSION = distinct run_id", r2["run_id"] != r1["run_id"])
    check("v1 and v2 produce DISTINCT output hashes (different packager)", r1["output_hash"] != r2["output_hash"])
    check("old v1 run still readable after v2 run", ledger.get_run(r1["run_id"])["status"] == "done")
    rec2 = ledger.get_run(r2["run_id"])
    pkg_step = next(s for s in rec2["steps"] if s["step_id"] == "package")
    check("v2 lineage shows package.context_pack@v2 (processor swapped by manifest)", pkg_step["processor"] == "package.context_pack@v2")
    pack2 = ledger.get_artifact(r2["artifact_ids"]["ContextPack.v1"])["payload"]
    check("v2 pack carries the v2-only fact_index (real swap, not relabel)", "fact_index" in pack2 and pack2["kind"] == "baltor.context-pack.v2")

    # ── multi-grain decomposer as a processor-version swap (v3 side-by-side) ──
    v3 = specs["cfpb_structured_ingest@v3"]
    check("v3 validates clean (multigrain@v2 registered)", validate(v3, registry=reg) == [], str(validate(v3, registry=reg)))
    r3 = run_pipeline(v3, tenant_id="acme", run_input=run_input, ledger=ledger, registry=reg)
    check("v3 (multigrain) run reaches done", r3["status"] == "done", str(r3))
    rec3 = ledger.get_run(r3["run_id"])
    dec_step = next(s for s in rec3["steps"] if s["step_id"] == "decompose")
    check("v3 lineage shows decompose.multigrain@v2 (grain = processor-version swap)", dec_step["processor"] == "decompose.multigrain@v2")
    mg = ledger.get_artifact(r3["artifact_ids"]["MultiGrainSet.v1"])["payload"]
    grains0 = mg["per_record"][0]["grains"]
    check("v3 produced multi-grain artifact (facts+sentences+paragraphs+conclusion+sentiment)",
          set(grains0) == {"fact", "sentence", "paragraph", "conclusion", "sentiment"})
    check("v3 carries a sentiment signal per record", "polarity" in mg["per_record"][0]["sentiment"])
    check("v1 and v3 produce DISTINCT output hashes (different grain)", r3["output_hash"] != r1["output_hash"])
    check("v1, v2, v3 all readable side-by-side", all(ledger.get_run(r["run_id"])["status"] == "done" for r in (r1, r2, r3)))

    # ── unstructured seam (experimental, unavailable) ──
    seam = specs["unstructured_pdf_docling@v0"]
    rs = run_pipeline(seam, tenant_id="acme", run_input=run_input, ledger=ledger, registry=reg)
    check("experimental docling run FAILS with a clear unavailable_processor error (not a crash)",
          rs["status"] == "failed" and "unavailable_processor" in (rs.get("error") or ""))
    recs = ledger.get_run(rs["run_id"])
    check("the unavailable error is recorded in the run ledger", recs["status"] == "failed" and recs["error"] is not None)

    store.close()
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'PASS — check_pipeline_runtime: CFPB is now cfpb_structured_ingest@v1 on a generic runtime; versioned side-by-side, processor-swappable by manifest, reprocessing-aware, with a discoverable experimental Docling seam.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: Pipeline Runtime v1 (registry+run+versions+swap+seam).")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
