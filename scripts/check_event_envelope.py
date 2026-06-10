#!/usr/bin/env python3
"""scripts.check_event_envelope — proof of the C26 event-envelope contract, applied to REAL emits.

Unit: make_envelope is deterministic + complete; validate_envelope catches missing/bad fields;
validate_causality_chain rejects dangling causality. Integrated: run a real pipeline with a bus, lift
every emitted event onto an envelope (chained causation), and assert the whole chain validates + shares
one correlation_id + is a clean causality chain — i.e. the contract holds over actual runtime events.

CLI:
    python3 scripts/check_event_envelope.py --self-test
"""
from __future__ import annotations

import argparse
import shutil
import tempfile

from scripts.context_events import EventBus
from scripts.durable_store import DurableStore
from scripts.pipeline_runtime.envelope import (
    chain_events, envelope_from_event, make_envelope, validate_causality_chain, validate_envelope,
)
from scripts.pipeline_runtime.processors import default_registry
from scripts.pipeline_runtime.runner import run_pipeline
from scripts.pipeline_runtime.specs import discover
from scripts.pipeline_runtime.store import PipelineLedger


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # ── unit: envelope build + determinism ──
    e1 = make_envelope("pipeline.completed", payload={"x": 1}, correlation_id="run-1", subject_id="run-1",
                       pass_id="C36", engine="pipeline_runtime", engine_version="v1", priority="p0",
                       evidence={"input_hash": "sha256:a", "output_hash": "sha256:b"})
    check("envelope carries all required fields", validate_envelope(e1) == [], str(validate_envelope(e1)))
    check("event_id is content-addressed", e1["event_id"].startswith("evt-"))
    e1b = make_envelope("pipeline.completed", payload={"x": 1}, correlation_id="run-1", subject_id="run-1",
                        pass_id="DIFFERENT", engine="x", evidence={})  # identity fields same → same id
    check("deterministic event_id over identity fields (metadata-independent)", e1b["event_id"] == e1["event_id"])

    # ── unit: validation catches bad envelopes ──
    bad = dict(e1)
    del bad["idempotency_key"]
    check("missing required field rejected", validate_envelope(bad) != [])
    badp = dict(e1)
    badp["priority"] = "urgent"
    check("invalid priority rejected", any("priority" in x for x in validate_envelope(badp)))
    bada = dict(e1)
    bada["attempt"] = 0
    check("attempt < 1 rejected", any("attempt" in x for x in validate_envelope(bada)))

    # ── unit: causality chain ──
    root = make_envelope("pipeline.started", correlation_id="r", subject_id="r")
    child = make_envelope("pipeline.completed", correlation_id="r", subject_id="r", causation_id=root["event_id"])
    check("valid chain (child causation → known root) passes", validate_causality_chain([root, child]) == [])
    orphan = make_envelope("pipeline.completed", correlation_id="r", subject_id="r", causation_id="evt-nonexistent")
    check("dangling causation rejected", validate_causality_chain([root, orphan]) != [])

    # ── integrated: apply the envelope to a REAL pipeline run's emitted events ──
    tmp = tempfile.mkdtemp(prefix="env-proof-")
    store = DurableStore(tmp + "/d.db")
    ledger = PipelineLedger(store)
    bus = EventBus()
    seen: list[dict] = []
    bus.subscribe(seen.append)
    spec = discover()["cfpb_structured_ingest@v1"]
    res = run_pipeline(spec, tenant_id="acme", run_input={"fixture": True, "limit": 5, "source_id": "cfpb"},
                       ledger=ledger, registry=default_registry(), bus=bus)
    check("real run emitted events onto the bus", len(seen) >= 3 and res["status"] == "done", str(len(seen)))
    envs = chain_events(seen, pass_id="C36", engine_version="v1")
    check("every real emit lifts to a VALID envelope", all(validate_envelope(e) == [] for e in envs))
    check("real-emit chain is a clean causality chain", validate_causality_chain(envs) == [])
    check("all events of the run share ONE correlation_id (the run id)",
          len({e["correlation_id"] for e in envs}) == 1 and envs[0]["correlation_id"] == res["run_id"])
    check("first envelope is the root (no causation); rest are caused",
          envs[0]["causation_id"] == "" and all(e["causation_id"] for e in envs[1:]))
    check("envelope idempotency keys are unique per emit", len({e["idempotency_key"] for e in envs}) == len(envs))

    store.close()
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'PASS — check_event_envelope: C26 envelope contract holds (deterministic id, validation, causality) and applies cleanly to the emitted events of a REAL pipeline run.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: C26 event-envelope contract over real emits.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
