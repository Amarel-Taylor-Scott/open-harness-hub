#!/usr/bin/env python3
"""scripts.check_context_audit_bridge — PROOF: the Context Auditor is CONNECTED to the running system.

The auditor emits one event per finding onto the shared bus (scripts.context_events) and exposes a governed
gateway PRE-CALL path. Asserts:
  A. audit_and_emit fires the right event per issue — conflict→contradiction_found, stale→rot.detected,
     duplicate→context.duplicate_found, tool_bloat→context.tool_bloat — plus a context.audited summary; every
     event is component=context_auditor, carries the correlation_id, and has a monotonic seq (no wall-clock).
  B. the report is unchanged by emitting (== a bare audit()); the bridge is lossless.
  C. PROPOSES not disposes — the context.audited summary carries applied=False; events are signals.
  D. the gateway PRE-CALL path (audited_pre_call) ends with inference.requested carrying the manifest
     (audited=True), so the gateway only ever sees an audited bundle.
  E. every auditor ISSUE_TYPE maps to an event kind (no silent un-emitted finding); no raw secrets.

Deterministic, offline, stdlib-only. Exit 0/1. `--self-test` runs the gate (also the default body).
"""
from __future__ import annotations

import json
import re
import sys

from scripts.context_events import EVENT_KINDS, EventBus
from src.baltor.context_audit.audit_bridge import _ISSUE_EVENT, audit_and_emit, audited_pre_call, optimize_pre_call
from src.baltor.context_audit.context_auditor import ISSUE_TYPES, _fixture, audit

_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,})")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # E (static): every issue type maps to an event kind, and every mapped kind is a real EVENT_KIND
    ck("E: every ISSUE_TYPE maps to an event kind", set(_ISSUE_EVENT) == set(ISSUE_TYPES))
    ck("E: every mapped kind is in EVENT_KINDS (single source)",
       all(kind in EVENT_KINDS for kind, _stage in _ISSUE_EVENT.values()), str(sorted(_ISSUE_EVENT.values())))
    ck("E: the summary kind context.audited is in EVENT_KINDS", "context.audited" in EVENT_KINDS)

    # A. audit_and_emit fires the expected events
    bus = EventBus()
    report = audit_and_emit(_fixture(), bus, correlation_id="cid-1")
    evs = bus.recent(50)
    kinds = [e["kind"] for e in evs]
    for k in ("contradiction_found", "rot.detected", "context.duplicate_found", "context.tool_bloat", "context.audited", "context.poisoning_suspected"):
        ck(f"A: emitted {k}", k in kinds, str(kinds))
    ck("A: every event is from component=context_auditor", all(e["component"] == "context_auditor" for e in evs))
    ck("A: every event carries the correlation_id", all(e["correlation_id"] == "cid-1" for e in evs))
    seqs = [e["seq"] for e in evs]
    ck("A: monotonic seq (no wall-clock), strictly increasing", seqs == sorted(seqs) and len(set(seqs)) == len(seqs))

    # B. lossless — the report equals a bare audit() of the same fixture
    ck("B: report unchanged by emitting (== bare audit)", report == audit(_fixture()))

    # C. proposes not disposes — the summary says applied=False
    summary = [e for e in evs if e["kind"] == "context.audited"][0]
    ck("C: context.audited summary carries applied=False", summary["payload"]["applied"] is False)
    ck("C: summary counts match the report", summary["payload"]["issue_count"] == len(report["issues"]))

    # D. gateway pre-call path ends with an audited inference.requested
    bus2 = EventBus()
    audited_pre_call(_fixture(), bus2, correlation_id="cid-2", model_hint="local")
    last = bus2.recent(50)[-1]
    ck("D: pre-call path ends with inference.requested", last["kind"] == "inference.requested")
    ck("D: inference.requested carries the audited manifest", last["payload"]["audited"] is True and last["payload"]["applied"] is False)

    # D2. optimize_pre_call: audit → emit → APPLY (lossless) — emits context.optimized + returns the optimized bundle
    bus3 = EventBus()
    pre = optimize_pre_call(_fixture(), bus3, correlation_id="cid-3")
    k3 = [e["kind"] for e in bus3.recent(50)]
    ck("D2: optimize_pre_call emits context.audited", "context.audited" in k3)
    ck("D2: optimize_pre_call emits context.optimized", "context.optimized" in k3, str(sorted(set(k3))))
    ck("D2: returns the optimized bundle + a lossless envelope",
       isinstance(pre.get("optimized"), list) and pre["envelope"]["lossless"] is True and pre["envelope"]["rehydratable"] is True)
    ck("D2: optimized has fewer tokens than original",
       pre["envelope"]["optimized_tokens"] < pre["envelope"]["original_tokens"])
    co = [e for e in bus3.recent(50) if e["kind"] == "context.optimized"]
    ck("D2: context.optimized from component=context_optimizer", bool(co) and co[0]["component"] == "context_optimizer")

    # E. no secrets in the emitted stream
    ck("E: no raw keys in the emitted events", not _KEY_RE.search(json.dumps(evs)))

    print("\n" + ("PASS — check_context_audit_bridge: the Context Auditor is CONNECTED — it emits one bus event per "
                  "finding (conflict→contradiction_found, stale→rot.detected, duplicate/bloat→Optimization signals) "
                  "+ a context.audited summary, with monotonic seq; the gateway pre-call path attaches the manifest "
                  "to inference.requested; lossless + proposes-not-disposes."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_context_audit_bridge.py --self-test")
    raise SystemExit(0)
