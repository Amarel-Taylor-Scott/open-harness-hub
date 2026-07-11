#!/usr/bin/env python3
"""scripts.check_context_audit_in_pipeline — PROOF: the Context Auditor fires INSIDE the connected pipeline.

run_full_pipeline now audits the assembled context (_repos/baltor/backend/src/baltor/context_audit/audit_bridge.audit_and_emit) so
the auditor is VISIBLE on /dashboard — its distinctive REDUNDANT/bloat signals (context.duplicate_found /
context.tool_bloat) plus a context.audited manifest fire mid-run, alongside the existing engine events. Drives
run_full_pipeline over a fresh in-process bus (offline, no Redis) and asserts:
  A. the auditor fires — context.audited + context.duplicate_found + context.tool_bloat are emitted, within the
     pipeline.started → pipeline.completed span, from component=context_auditor.
  B. PROPOSES not disposes — the context.audited summary carries applied=False (a manifest, not an action).
  C. NO REGRESSION — the core pipeline kinds still fire AND exactly ONE inference.requested (the audit step
     used audit_and_emit, not audited_pre_call — it must not inject a second inference request).
  D. the return dict carries the audit summary; the served answer is unchanged (answer_value == 5).
  E. DETERMINISM — two runs over fresh buses emit the same event-kind sequence.
  F. no raw secrets in any auditor event.

Deterministic, offline, stdlib-only. Exit 0/1. `--self-test` runs the gate (also the default body).
"""
from __future__ import annotations

import json
import re
import sys

from scripts.baltor_admin_demo_server import run_full_pipeline
from scripts.context_events import EventBus

_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,})")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    bus = EventBus()
    out = run_full_pipeline(bus)
    events = bus.recent(2000)
    kinds = [e["kind"] for e in events]

    # A. the auditor fires, within the pipeline span, from the auditor component
    for k in ("context.audited", "context.duplicate_found", "context.tool_bloat"):
        ck(f"A: {k} fired", k in kinds, str(sorted(set(kinds))))
    if "pipeline.started" in kinds and "pipeline.completed" in kinds:
        i0, i1 = kinds.index("pipeline.started"), kinds.index("pipeline.completed")
        ck("A: context.audited fires within the pipeline span",
           any(k == "context.audited" and i0 < j < i1 for j, k in enumerate(kinds)))
    aud = [e for e in events if e["kind"] == "context.audited"]
    ck("A: context.audited from component=context_auditor", bool(aud) and aud[0]["component"] == "context_auditor")

    # B. proposes not disposes
    ck("B: context.audited summary carries applied=False", bool(aud) and aud[0]["payload"].get("applied") is False)
    ck("B: summary reports >=2 issues (duplicate + tool_bloat)", bool(aud) and aud[0]["payload"].get("issue_count", 0) >= 2)

    # A2. the OPTIMIZER step also fires (context.optimized) + the gateway pre-call sees the optimized bundle
    ck("A2: context.optimized fired", "context.optimized" in kinds, str(sorted(set(kinds))))
    infreq = [e for e in events if e["kind"] == "inference.requested"]
    ck("A2: inference.requested sees the optimized bundle (context_optimized=True)",
       bool(infreq) and infreq[0]["payload"].get("context_optimized") is True)
    ck("A2: return carries optimized_tokens + lossless flag",
       out.get("context_audit", {}).get("optimized_tokens", 0) >= 1 and out["context_audit"].get("lossless") is True)

    # C. no regression + exactly one inference request (audit_and_emit, NOT audited_pre_call)
    for need in ("pipeline.started", "context_object.created", "inference.requested",
                 "inference.completed", "receipt_issued", "pipeline.completed"):
        ck(f"C: core kind {need} still fires", need in kinds)
    ck("C: exactly one inference.requested (audit added none)", kinds.count("inference.requested") == 1, str(kinds.count("inference.requested")))

    # D. return summary + unchanged answer
    ck("D: return carries the context_audit summary", out.get("context_audit", {}).get("issues", 0) >= 2)
    ck("D: served answer unchanged (answer_value == 5)", out.get("answer_value") == 5, str(out.get("answer_value")))

    # E. determinism — same kind sequence on a second fresh run
    bus2 = EventBus()
    run_full_pipeline(bus2)
    kinds2 = [e["kind"] for e in bus2.recent(2000)]
    ck("E: two runs emit the same event-kind sequence", kinds == kinds2)

    # F. no secrets in auditor events
    audit_evs = [e for e in events if e.get("component") == "context_auditor"]
    ck("F: no raw keys in auditor events", not _KEY_RE.search(json.dumps(audit_evs)))

    print("\n" + ("PASS — check_context_audit_in_pipeline: the Context Auditor fires live inside run_full_pipeline "
                  "(context.audited + context.duplicate_found + context.tool_bloat within the pipeline span, from "
                  "context_auditor, applied=False), no regression (core kinds + exactly one inference request), "
                  "deterministic across runs."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_context_audit_in_pipeline.py --self-test")
    raise SystemExit(0)
