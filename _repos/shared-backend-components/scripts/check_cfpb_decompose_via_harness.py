#!/usr/bin/env python3
"""scripts.check_cfpb_decompose_via_harness — proof: the EXISTING CFPB structured decomposition runs through
the standard ProcessorHarness without regression — emitting atomic_fact + narrative_allegation
ArtifactEnvelopes that keep their #field source handles and governance (facts promotable, allegations not).

CLI: python3 _repos/shared-backend-components/scripts/check_cfpb_decompose_via_harness.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.runtime.context import build_context
from scripts.runtime.envelopes import CommandEnvelope
from scripts.runtime.processor_harness import run_command
from scripts.runtime.processor_registry import default_registry

REC = {"complaint_id": "CFPB-1", "product": "Credit card", "issue": "Billing dispute", "company": "Acme Bank",
       "state": "CA", "date_received": "2026-01-02",
       "consumer_complaint_narrative": "I was charged twice. The company refused to refund me. This is unfair."}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    ctx = build_context(tenant_id="acme", run_id="run-cfpb", pipeline_id="cfpb_artifact_graph",
                        pipeline_version="v1", step_id="decompose")
    cmd = CommandEnvelope(command_type="pipeline.run_step", tenant_id="acme", run_id="run-cfpb", queue="q",
                          pipeline_id="cfpb_artifact_graph", pipeline_version="v1", step_id="decompose",
                          processor_id="decompose.cfpb_structured", processor_version="v1", payload={"records": [REC]})
    out = run_command(default_registry(), cmd, ctx)
    check("CFPB record runs through the harness OK", out["ok"], str(out.get("error")))

    arts = out["result"]["artifacts"]
    facts = [a for a in arts if a["artifact_type"] == "atomic_fact"]
    alleg = [a for a in arts if a["artifact_type"] == "narrative_allegation"]
    check("emits atomic_fact ArtifactEnvelopes", len(facts) >= 5, str(len(facts)))
    check("emits narrative_allegation ArtifactEnvelopes (3 sentences)", len(alleg) == 3, str(len(alleg)))

    check("atomic facts are promotion_eligible=true", all(f["governance"]["promotion_eligible"] is True for f in facts))
    check("narrative allegations are promotion_eligible=false", all(a["governance"]["promotion_eligible"] is False for a in alleg))
    check("facts keep their #field source handles", all("#" in (f["payload"].get("source_handle") or "") for f in facts))
    check("allegations require human review", all(a["governance"]["requires_human_review"] is True for a in alleg))

    check("every emitted artifact carries full lineage (run/pipeline/processor)",
          all(a["lineage"]["run_id"] == "run-cfpb" and a["lineage"]["processor_id"] == "decompose.cfpb_structured" for a in arts))
    check("every artifact has a content_hash + security envelope",
          all(a["content_hash"].startswith("sha256:") and a["security"]["classification"] for a in arts))

    # parity with the legacy path (no regression in counts)
    from scripts.ingest.decompose_structured import decompose_cfpb_complaint, CLAIM_FACT
    legacy = decompose_cfpb_complaint(REC, native_id="cfpb:CFPB-1")["components"]
    legacy_facts = sum(1 for c in legacy if c["claim_status"] == CLAIM_FACT)
    check("fact count matches the legacy decomposition (no regression)", len(facts) == legacy_facts, f"{len(facts)} vs {legacy_facts}")

    print(f"\n{'PASS — check_cfpb_decompose_via_harness: existing CFPB decomposition runs through the harness, emits governed atomic_fact + narrative_allegation envelopes with #field handles + lineage, no regression.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: CFPB decomposition via the harness.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
