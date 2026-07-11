#!/usr/bin/env python3
"""scripts.check_shared_inference_io — PROOF: the inference I/O layer (InferenceRequest + ModelRouteDecision)
projects the LIVE Inference Gateway honestly — request carries an input HASH not raw text; the route decision
records the governed-fallback trail; the receipt's allowed_use is never 'served'.

Asserts:
  A. CONTRACTS: InferenceRequest + ModelRouteDecision registered.
  B. REQUEST: make_inference_request conforms to InferenceRequest; carries input_hash; the RAW prompt text is
     NOT present anywhere in the request (privacy).
  C. ROUTE (clean): a credentialed preferred external node selects without fallback; project_route_decision
     conforms to ModelRouteDecision.
  D. ROUTE (governed fallback): with no credentials the gateway falls back (fallback_used, reason codes recorded,
     not silent); still conforms; blocked is a boolean.
  E. RECEIPT: infer_local's receipt conforms to ModelInvocationReceipt and allowed_use is never 'served'.
  F. DETERMINISM + DEPENDENCY LAW: projectors pure; _repos/teleon/backend/src/teleon/io never imports src.baltor.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.inference import oips
from src.teleon.io import make_inference_request, project_route_decision

_NOW = "2026-06-07T00:00:00Z"


def _required(rel: str) -> list[str]:
    return json.loads((_resource("schemas") / rel).read_text())["required"]


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    def conforms(rec: dict, rel: str) -> bool:
        return all(k in rec for k in _required(rel))

    contracts = json.dumps(json.loads((_resource("architecture") / "contract_registry.json").read_text()))
    check("A: InferenceRequest + ModelRouteDecision registered",
          "inference/InferenceRequest.schema.json" in contracts and "inference/ModelRouteDecision.schema.json" in contracts)

    secret = "super-secret-prompt-body-xyz"
    req = make_inference_request(object_id="obj-1", requested_model_class="tier:500/[500]",
                                 input_text=secret, now=_NOW, preference_id="pref-1")
    check("B: request conforms + input hashed + raw text absent",
          conforms(req, "inference/InferenceRequest.schema.json") and req["input_hash"].startswith("sha256:")
          and secret not in json.dumps(req), json.dumps(req))

    pref = [{"preference_id": "pref-1",
             "model_class_preference": {"tier_code": 500, "specialization_codes": [500]},
             "allowed_provider_nodes": ["model.anthropic.frontier@candidate", "model.local_stub@v1"],
             "disallowed_provider_nodes": [], "fallback_policy": {}, "data_policy": {}}]
    resolved = oips.resolve_preference(pref)

    route_clean = oips.select_provider(resolved, available_secrets={"secret://provider/anthropic"})
    rc = project_route_decision(route_clean)
    check("C: credentialed preferred node selected, no fallback; route conforms",
          rc.get("selected_provider_node_id") == "model.anthropic.frontier@candidate" and rc.get("fallback_used") is False
          and conforms(rc, "inference/ModelRouteDecision.schema.json"), json.dumps(rc))

    route_fb = oips.select_provider(resolved, available_secrets=set())
    rf = project_route_decision(route_fb)
    check("D: no creds -> governed fallback recorded (not silent); conforms; blocked is bool",
          rf.get("fallback_used") is True and rf.get("fallback_reason_codes") and isinstance(rf.get("blocked"), bool)
          and conforms(rf, "inference/ModelRouteDecision.schema.json"), json.dumps(rf))

    res = oips.infer_local(object_id="obj-1", preference_layers=pref, input_text=secret, now=_NOW)
    rcpt = res["receipt"]
    check("E: receipt conforms + allowed_use never 'served'",
          conforms(rcpt, "inference/ModelInvocationReceipt.schema.json") and rcpt["allowed_use"] != "served", rcpt.get("allowed_use"))

    check("F: projectors deterministic",
          project_route_decision(route_clean) == rc and make_inference_request(object_id="obj-1", requested_model_class="tier:500/[500]", input_text=secret, now=_NOW, preference_id="pref-1") == req)
    src = "\n".join(p.read_text() for p in (_resource("src/teleon/io")).rglob("*.py"))
    check("F: _repos/teleon/backend/src/teleon/io never imports src.baltor",
          not any(l.strip().startswith(("import src.baltor", "from src.baltor")) for l in src.splitlines()))

    print("\n" + ("PASS — check_shared_inference_io: InferenceRequest carries an input hash (never raw text); "
                  "ModelRouteDecision names the gateway's selection with the recorded governed-fallback trail; the "
                  "receipt conforms and is never 'served'; pure projectors; Teleon-side."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_shared_inference_io.py --self-test")
    raise SystemExit(0)
