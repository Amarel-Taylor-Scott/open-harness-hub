#!/usr/bin/env python3
"""scripts.check_inference_dispatch_via_adapters — PROOF: the Inference Gateway's infer_local now DISPATCHES execution
through the standardized provider-adapter layer (the adapter base class is the live backbone) — not a hardcoded stub —
while preserving the exact offline contract.

Asserts:
  A. WIRED: oips.infer_local routes execution through adapters.resolve_adapter (the dispatch is present in its source).
  B. NOT INLINED: the deterministic-stub output string is NO LONGER hardcoded inside infer_local — it lives in the
     LocalStubAdapter (execution is delegated to the adapter, not duplicated in the gateway).
  C. CONSISTENT: infer_local's output for a stub-pref is byte-identical to LocalStubAdapter.invoke (the dispatch really
     runs the adapter; the byte-identity that de-risked this wiring still holds).
  D. GOVERNED FALLBACK preserved: an external decided node offline (no secret/network) degrades to the local stub,
     fallback_used=true with reason codes recorded, output is_truth=false.
  E. OFFLINE-SAFE DEFAULT: infer_local exposes allow_network defaulting to False (live calls are opt-in/owner-gated).
  F. DETERMINISM.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.inference import oips
from src.teleon.inference import adapters as A

_NOW = "2026-06-05T00:00:00Z"
_STUB_PREF = [{"preference_id": "p", "model_class_preference": {"tier_code": 100, "specialization_codes": [300]},
               "allowed_provider_nodes": ["model.local_stub@v1"], "disallowed_provider_nodes": [],
               "fallback_policy": {}, "data_policy": {}}]
_EXT_PREF = [{"preference_id": "p", "model_class_preference": {"tier_code": 600, "specialization_codes": [500]},
              "allowed_provider_nodes": ["model.anthropic.frontier@candidate", "model.local_stub@v1"],
              "disallowed_provider_nodes": [], "fallback_policy": {}, "data_policy": {}}]


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    src = inspect.getsource(oips.infer_local)
    check("A: infer_local dispatches through adapters.resolve_adapter", "resolve_adapter" in src)
    adapters_src = inspect.getsource(A)
    check("B: the stub output string is delegated to LocalStubAdapter, not inlined in infer_local",
          "[local-stub deterministic output" not in src and "[local-stub deterministic output" in adapters_src)

    nodes = {n["node_id"]: n for n in oips.load_graph()["nodes"]}
    via_gateway = oips.infer_local(object_id="o", preference_layers=_STUB_PREF, input_text="hi", now=_NOW)["output"]
    via_adapter = A.resolve_adapter(nodes["model.local_stub@v1"]).invoke(object_id="o", input_text="hi", now=_NOW)["output"]
    check("C: gateway output == LocalStubAdapter output (dispatch runs the adapter; byte-identical)", via_gateway == via_adapter)

    ext = oips.infer_local(object_id="o", preference_layers=_EXT_PREF, input_text="hi", now=_NOW, available_secrets=set())
    rc = ext["receipt"]
    check("D: external decided node offline degrades to the stub, fallback recorded, output not truth",
          rc["selected_provider_node_id"] == oips.OFFLINE_DEFAULT_NODE and rc["fallback_used"] is True
          and bool(rc["fallback_reason_codes"]) and rc["policy_checks"]["llm_output_is_truth"] is False)

    sig = inspect.signature(oips.infer_local)
    check("E: infer_local exposes allow_network defaulting to False (live calls opt-in)",
          "allow_network" in sig.parameters and sig.parameters["allow_network"].default is False)

    again = oips.infer_local(object_id="o", preference_layers=_STUB_PREF, input_text="hi", now=_NOW)["output"]
    check("F: deterministic (same inputs -> same output)", again == via_gateway)

    print("\n" + ("PASS — check_inference_dispatch_via_adapters: infer_local now executes through the provider-adapter "
                  "registry (the base class is the live backbone), the stub output is delegated not inlined, the output "
                  "stays byte-identical, governed fallback to the stub holds offline, and live calls are opt-in."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_inference_dispatch_via_adapters.py --self-test")
    raise SystemExit(0)
