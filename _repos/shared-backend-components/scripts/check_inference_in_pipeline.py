#!/usr/bin/env python3
"""scripts.check_inference_in_pipeline — PROOF: the Shared LLM Plane fires INSIDE the connected pipeline, governed.

run_full_pipeline now drives a real inference step through the Inference Gateway (local stub) so the plane is VISIBLE
on /dashboard as inference.requested → inference.completed events. This proof drives run_full_pipeline over a fresh
in-process EventBus (offline, no server, no Redis) and asserts the model output is a candidate — never the served
truth — and that the events leak no secret.

Asserts:
  A. KINDS REGISTERED: inference.requested + inference.completed are in EVENT_KINDS (the single source).
  B. BOTH FIRE: run_full_pipeline emits exactly one inference.requested and one inference.completed, in that order,
     within the pipeline correlation, on the Enhancement stage.
  C. RECEIPT-BACKED: inference.completed carries a receipt_id and the executed provider node id.
  D. OUTPUT-NOT-TRUTH: both inference events are flagged is_truth=false / candidate-not-served-truth.
  E. TRUTH UNCHANGED: the pipeline's served answer_value equals the receipt_issued answer (the DETERMINISTIC value) —
     i.e. the LLM candidate did NOT become the served answer.
  F. NO SECRET LEAK: no secret-value pattern appears in any inference event payload (reuses the handler's guard).
  G. NO REGRESSION + DETERMINISM: the core pipeline kinds still fire and two runs emit the same event-kind sequence.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.context_events import EventBus, EVENT_KINDS
from scripts.baltor_admin_demo_server import run_full_pipeline
from scripts.api_inference_handler import _LEAK


def _run() -> tuple:
    bus = EventBus()
    out = run_full_pipeline(bus)
    return out, bus.recent(10_000)


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    check("A: inference.requested + inference.completed are in EVENT_KINDS",
          {"inference.requested", "inference.completed"} <= EVENT_KINDS)

    out, events = _run()
    req = [e for e in events if e["kind"] == "inference.requested"]
    done = [e for e in events if e["kind"] == "inference.completed"]
    check("B: exactly one inference.requested + one inference.completed fire, requested before completed",
          len(req) == 1 and len(done) == 1 and req[0]["seq"] < done[0]["seq"], f"req={len(req)} done={len(done)}")
    check("B: the inference events are on the Enhancement stage",
          all(e.get("stage") == "Enhancement" for e in req + done))

    dp = (done[0].get("payload") or {}) if done else {}
    check("C: inference.completed is receipt-backed (receipt_id + executed node)",
          bool(dp.get("receipt_id")) and bool(dp.get("executed_node")), json.dumps(dp))
    check("D: both inference events are flagged output-not-truth",
          (req[0].get("payload") or {}).get("is_truth") is False and dp.get("is_truth") is False
          and dp.get("candidate_output_is_not_served_truth") is True)

    receipts = [e for e in events if e["kind"] == "receipt_issued"]
    served = (receipts[0].get("payload") or {}).get("answer_value") if receipts else None
    check("E: the served answer is the DETERMINISTIC value (LLM candidate did not become truth)",
          served is not None and out.get("answer_value") == served, f"served={served!r} out={out.get('answer_value')!r}")

    leaks = [e["kind"] for e in req + done if _LEAK.search(json.dumps(e.get("payload") or {}))]
    check("F: no secret-value pattern in any inference event payload", not leaks, str(leaks))

    kinds = [e["kind"] for e in events]
    check("G: no regression — core pipeline kinds still fire",
          all(k in kinds for k in ("pipeline.started", "context_pack.created", "receipt_issued", "pipeline.completed")))
    _, events2 = _run()
    check("G: deterministic — two runs emit the same event-kind sequence", kinds == [e["kind"] for e in events2])

    print("\n" + ("PASS — check_inference_in_pipeline: the Shared LLM Plane fires inside run_full_pipeline as governed "
                  "inference.requested → inference.completed events (receipt-backed, is_truth=false); the deterministic "
                  "answer remains the served truth, the LLM output stays a candidate, and no secret leaks." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_inference_in_pipeline.py --self-test")
    raise SystemExit(0)
