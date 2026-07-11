#!/usr/bin/env python3
"""scripts.check_pipeline_lineage — proof: a run's full lineage projection (steps + artifacts + span tree).

`run_lineage` assembles, from the durable ledger + persisted events (source of truth), a run's step_runs,
content-addressed artifacts, and the OTel span tree — the data a /dev or /raw view renders. Proven over a
REAL run end-to-end: every step + artifact present, the span tree is valid (one trace_id = run id, parent
links resolve), and an unknown run id returns no lineage.

CLI:
    python3 _repos/shared-backend-components/scripts/check_pipeline_lineage.py --self-test
"""
from __future__ import annotations

import argparse
import shutil
import tempfile

from scripts.context_events import EventBus
from scripts.durable_store import DurableStore
from scripts.pipeline_runtime.otel import validate_span_tree
from scripts.pipeline_runtime.processors import default_registry
from scripts.pipeline_runtime.runner import run_lineage, run_pipeline
from scripts.pipeline_runtime.specs import discover
from scripts.pipeline_runtime.store import PipelineLedger


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    tmp = tempfile.mkdtemp(prefix="lineage-proof-")
    store = DurableStore(tmp + "/d.db")
    ledger = PipelineLedger(store)
    bus = EventBus()
    bus.subscribe(store.append_event)  # persist the run's events so lineage can rebuild the span tree
    spec = discover()["cfpb_structured_ingest@v1"]
    res = run_pipeline(spec, tenant_id="acme", run_input={"fixture": True, "limit": 5, "source_id": "cfpb"},
                       ledger=ledger, registry=default_registry(), bus=bus)
    check("run done", res["status"] == "done", str(res["status"]))

    lin = run_lineage(ledger, store, res["run_id"])
    check("lineage returns the run", lin and lin["run"]["run_id"] == res["run_id"])
    check("lineage lists all 4 step_runs (done)",
          len(lin["run"]["steps"]) == 4 and all(s["status"] == "done" for s in lin["run"]["steps"]))
    check("lineage lists content-addressed artifacts with their step_id",
          len(lin["artifacts"]) >= 4 and all(a["content_hash"] and a["step_id"] for a in lin["artifacts"]))
    check("lineage carries a non-empty OTel span tree", lin["span_count"] >= 3, str(lin["span_count"]))
    check("the span tree is VALID (one trace_id, parents resolve, single root)", validate_span_tree(lin["spans"]) == [])
    check("span tree trace_id == run_id", all(s["trace_id"] == res["run_id"] for s in lin["spans"]))
    check("ContextPack artifact appears in the lineage", any(a["artifact_type"] == "ContextPack" for a in lin["artifacts"]))
    check("unknown run id → no lineage", run_lineage(ledger, store, "run-nope") is None)

    store.close()
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'PASS — check_pipeline_lineage: a run projects to a full lineage (steps + content-addressed artifacts + valid OTel span tree) from the durable ledger + event log; the dashboard renders this projection, not its own truth.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: run lineage projection (steps + artifacts + span tree).")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
