#!/usr/bin/env python3
"""scripts.check_pipeline_unstructured — proof: an UNSTRUCTURED document runs end-to-end to a tree.

`unstructured_doc_tree@v1` runs offline behind a CannedParser: raw document → recursive ContextObject
tree (pages/paragraphs/tables/figures/OCR spans) with coordinate-precise `ctx://…#` leaf handles, per-node
lineage, low-confidence flags — content-addressed, gated, in the durable run ledger. The real-Docling
variant (`unstructured_pdf_docling@v0`) stays discoverable + experimental + fails with a clear
unavailable_processor error (the vendored-dep swap). This proves the unstructured grain works on the SAME
generic runtime as the structured CFPB pipeline — only the ParserProvider differs.

CLI:
    python3 scripts/check_pipeline_unstructured.py --self-test
"""
from __future__ import annotations

import argparse
import shutil
import tempfile

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
    spec = specs.get("unstructured_doc_tree@v1")
    check("unstructured_doc_tree@v1 discovered + active", spec and spec.status == "active")
    check("unstructured pipeline validates (parser.document_tree@v1 registered)", validate(spec, registry=reg) == [], str(validate(spec, registry=reg)))

    tmp = tempfile.mkdtemp(prefix="pipe-unstruct-")
    store = DurableStore(tmp + "/d.db")
    ledger = PipelineLedger(store)

    r = run_pipeline(spec, tenant_id="acme", run_input={"doc_id": "policy-001", "source_id": "acme-docs"},
                     ledger=ledger, registry=reg)
    check("unstructured run reaches done", r["status"] == "done", str(r))
    check("gate document_tree_has_addressable_leaves passed", r["failed_gates"] == [], str(r.get("gates")))
    tree = ledger.get_artifact(r["artifact_ids"]["DocumentTree"])["payload"]
    check("tree has the recursive nodes (doc→pages→blocks→cells, >=10)", tree["node_count"] >= 10, str(tree["node_count"]))
    check("tree has 3 pages", tree["page_count"] == 3, str(tree["page_count"]))
    check("every leaf is addressable by a ctx:// fragment handle",
          tree["leaf_handles"] and all(h.startswith("ctx://") and "#" in h for h in tree["leaf_handles"]))
    check("low-confidence OCR span flagged for review", len(tree["low_confidence_handles"]) >= 1, str(tree["low_confidence_handles"]))
    check("tree artifact is content-addressed", ledger.get_artifact(r["artifact_ids"]["DocumentTree"])["content_hash"])

    # the REAL-Docling variant stays a clean unavailable seam (vendored-dep swap)
    seam = specs.get("unstructured_pdf_docling@v0")
    check("real-Docling variant still discoverable + experimental", seam and seam.status == "experimental")
    rs = run_pipeline(seam, tenant_id="acme", run_input={"limit": 5}, ledger=ledger, registry=reg)
    check("real-Docling variant fails with a CLEAR unavailable_processor error (not a crash)",
          rs["status"] == "failed" and "unavailable_processor" in (rs.get("error") or ""))

    store.close()
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'PASS — check_pipeline_unstructured: an unstructured document runs end-to-end (offline CannedParser) to an addressable ContextObject tree on the generic runtime; the real-Docling variant is a clean unavailable seam.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: unstructured document → addressable tree end-to-end.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
