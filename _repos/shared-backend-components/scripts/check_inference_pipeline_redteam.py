#!/usr/bin/env python3
"""scripts.check_inference_pipeline_redteam — ADVERSARIAL PROOF of the inference step inside run_full_pipeline.

The pipeline now drives a governed inference step (Shared LLM Plane) and emits inference.requested →
inference.completed. This redteam attacks that wiring: each attack below MUST fail safely. It complements
check_inference_in_pipeline (which proves the happy path) and check_inference_gateway_redteam (which attacks the
gateway in isolation) — here the target is specifically the PIPELINE integration.

Attacks (each must be blocked):
  A. SDK BYPASS: the governed inference path imports a provider SDK directly. -> none present.
  B. RAW KEY: the governed inference path reads a raw API key from the environment. -> none present.
  C. PROVENANCE: a receipt omits the actual provider node / model. -> both always recorded.
  D. SILENT FALLBACK: a preferred external (uncredentialed) node falls back without recording it. -> fallback_used
     + non-empty fallback_reason_codes are recorded (never silent).
  E. PROMOTED FALLBACK: a lower-tier/fallback execution marks its output as truth. -> llm_output_is_truth stays false.
  F. NO NETWORK: run_full_pipeline opens a network connection. -> with socket.connect hard-blocked, the pipeline
     still completes and ZERO connection attempts are made (the LLM step executes the local stub, offline).
  G. OUTPUT-AS-TRUTH: the model's candidate output becomes the served answer or leaks onto a served surface.
     -> the served answer is the deterministic value; the model output text appears on NO event payload.
  H. UNGOVERNED EVENT: code can publish an inference event kind that is not in EVENT_KINDS. -> the bus rejects it.
  I. CORRELATION/PREFERENCE: an inference event omits correlation_id, or a route decision omits preference_id.
     -> both inference events carry correlation_id; the requested event + route decision carry preference_id.
  J. GATE BYPASS: the inference step runs without the governance gates. -> verification.* + context_pack.created
     still fire in the same run.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import os
import re
import socket
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.context_events import EventBus, EVENT_KINDS
from scripts.baltor_admin_demo_server import run_full_pipeline
from src.teleon.inference import oips

#: the governed inference path that pipeline code routes through (must stay SDK-free + raw-key-free).
_INF_PATH = ("_repos/teleon/backend/src/teleon/inference/oips.py", "_repos/teleon/backend/src/teleon/inference/api_projection.py",
             "scripts/api_inference_handler.py")
_SDK_IMPORTS = re.compile(r"^\s*(?:import|from)\s+(openai|anthropic|google\.generativeai|cohere|mistralai|groq|"
                          r"together|replicate|litellm|vertexai|boto3)\b", re.M)
_RAW_KEY = re.compile(r"(os\.environ|os\.getenv|getenv)\s*[\[(]\s*['\"][A-Za-z_]*(KEY|TOKEN|SECRET|APIKEY)[A-Za-z_]*['\"]")
#: a preference that PREFERS an uncredentialed external node — must force a recorded (non-silent) fallback.
_EXTERNAL = "model.anthropic.frontier@candidate"
_PREF_EXTERNAL = [{"preference_id": "redteam.prefer_external",
                   "model_class_preference": {"tier_code": 600, "specialization_codes": [500]},
                   "allowed_provider_nodes": [_EXTERNAL, "model.local_stub@v1"],
                   "disallowed_provider_nodes": [], "fallback_policy": {}, "data_policy": {}}]


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    # A + B — static scans of the governed inference path
    sdk_hits, key_hits = [], []
    for rel in _INF_PATH:
        txt = (_resource(rel)).read_text(encoding="utf-8")
        if _SDK_IMPORTS.search(txt):
            sdk_hits.append(rel)
        if _RAW_KEY.search(txt):
            key_hits.append(rel)
    check("A: no provider SDK import in the governed inference path", not sdk_hits, str(sdk_hits))
    check("B: no raw API-key env read in the governed inference path", not key_hits, str(key_hits))

    # C/D/E — provenance + non-silent fallback + no promotion, via the gateway with an uncredentialed external pref
    inf = oips.infer_local(object_id="redteam.obj", preference_layers=_PREF_EXTERNAL,
                           input_text="x", now="2026-06-05T00:00:00Z", available_secrets=set())
    rc = inf["receipt"]
    check("C: receipt records the actual provider node + model",
          bool(rc.get("selected_provider_node_id")) and bool(rc.get("selected_model")))
    check("D: fallback is NOT silent (fallback_used + reason codes recorded)",
          rc.get("fallback_used") is True and bool(rc.get("fallback_reason_codes")), json.dumps(rc.get("fallback_reason_codes")))
    check("D: the uncredentialed external node did NOT execute (local stub ran instead)",
          rc.get("selected_provider_node_id") == oips.OFFLINE_DEFAULT_NODE)
    check("E: fallback output is NOT promoted to truth", rc.get("policy_checks", {}).get("llm_output_is_truth") is False)

    # F — NO NETWORK: hard-block socket.connect, run the pipeline, assert it completes with zero attempts
    attempts: list = []
    real_connect, real_create = socket.socket.connect, socket.create_connection

    def _blocked_connect(self, address, *a, **k):  # noqa: ANN001
        attempts.append(address)
        raise OSError("REDTEAM: network blocked")

    def _blocked_create(address, *a, **k):  # noqa: ANN001
        attempts.append(address)
        raise OSError("REDTEAM: network blocked")

    pipeline_ok = False
    events: list = []
    try:
        socket.socket.connect = _blocked_connect
        socket.create_connection = _blocked_create
        bus = EventBus()
        out = run_full_pipeline(bus)
        events = bus.recent(10_000)
        pipeline_ok = bool(out.get("ok"))
    except Exception as exc:  # a network attempt (or any error) under the block is a failure to isolate
        check("F: run_full_pipeline completes offline (no network)", False, f"{type(exc).__name__}: {str(exc)[:80]} attempts={attempts[:2]}")
    finally:
        socket.socket.connect = real_connect
        socket.create_connection = real_create
    if pipeline_ok:
        check("F: run_full_pipeline completes offline with ZERO network attempts", not attempts, f"attempts={attempts[:3]}")

    req = [e for e in events if e["kind"] == "inference.requested"]
    done = [e for e in events if e["kind"] == "inference.completed"]
    served = next((e for e in events if e["kind"] == "receipt_issued"), {})
    served_answer = (served.get("payload") or {}).get("answer_value")

    # G — model output never becomes truth / never leaks onto a served surface
    model_out = oips.infer_local(object_id="obj-runbook", preference_layers=[{
        "preference_id": "pipeline.explain", "model_class_preference": {"tier_code": 400, "specialization_codes": [300]},
        "allowed_provider_nodes": ["model.local_stub@v1"], "disallowed_provider_nodes": [],
        "fallback_policy": {}, "data_policy": {}}],
        input_text=f"Explain the retry ceiling answer: {served_answer}", now="2026-06-05T00:00:00Z")["output"]
    leaked = [e["kind"] for e in events if model_out and model_out in json.dumps(e.get("payload") or {})]
    check("G: served answer is the deterministic value, not the model output", served_answer and served_answer != model_out)
    check("G: the model output text appears on NO event payload (not served/leaked)", not leaked, str(leaked))

    # H — the bus rejects an ungoverned inference event kind
    rejected = False
    try:
        EventBus().publish("inference.smuggle_truth", correlation_id="x")
    except ValueError:
        rejected = True
    check("H: the bus rejects an inference event kind not in EVENT_KINDS", rejected
          and "inference.smuggle_truth" not in EVENT_KINDS)

    # I — correlation_id on every inference event; preference_id on the request + route decision
    check("I: both inference events carry a correlation_id",
          bool(req) and bool(done) and all(e.get("correlation_id") for e in req + done))
    check("I: the inference.requested event carries preference_id",
          bool(req) and bool((req[0].get("payload") or {}).get("preference_id")))
    check("I: the route decision carries preference_id", bool(inf["resolved_preference"].get("preference_id")))

    # J — the governance gates still ran in the same pipeline (inference did not bypass them)
    kinds = {e["kind"] for e in events}
    check("J: governance gates fired in the same run (verification.* + context_pack.created)",
          {"verification.started", "verification.completed", "context_pack.created"} <= kinds)

    print("\n" + ("PASS — check_inference_pipeline_redteam: every attack on the pipeline inference wiring fails safely — "
                  "no SDK/raw-key in the governed path, fallback is recorded (never silent), output is never promoted "
                  "to truth, the pipeline runs with ZERO network, the model output never reaches a served surface, "
                  "ungoverned event kinds are rejected, and the governance gates still run." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_inference_pipeline_redteam.py --self-test")
    raise SystemExit(0)
