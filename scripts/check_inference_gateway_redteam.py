#!/usr/bin/env python3
"""scripts.check_inference_gateway_redteam — REDTEAM PROOF over the EXISTING shared LLM plane (src/teleon/inference).
Consolidates the inference safety boundaries as adversarial cases against the real gateway — it builds NO new
wrapper. Every attack must fail safely.

Attacks (all must fail safely):
  A. SILENT FALLBACK: a preferred external node with no creds must NOT be selected silently — the route records
     fallback_used + fallback_reason_codes (the fallback is provenance, never silent).
  B. OUTPUT-AS-TRUTH: infer_local's receipt allowed_use is NEVER "served" and policy_checks.llm_output_is_truth
     is False (Baltor governs serving; the gateway never serves truth).
  C. PROVENANCE HONESTY / NO LIVE NETWORK: offline, the EXECUTED node is the local stub even when a cloud node was
     preferred — the receipt records the node that actually ran (no overstated provenance, no network call).
  D. RAW KEY LEAK: a raw key in the input never appears in the receipt (only an input_hash).
  E. CLAWLESS != ENDPOINT: a browser/WebContainer runtime classifies as browser_agent_runtime, NOT an inference provider.
  F. SHARED-KEY QUARANTINE: a shared-key/bypass repo classifies into the quarantine band.
  G. FREE + SENSITIVE: an official free/limited endpoint may NOT take customer-sensitive data (policy fail-closed).
  H. SECRET REFS ONLY: every external provider node carries a secret:// ref; no raw key appears anywhere in the graph.
  I. NUMERIC ROUTING: with creds the gateway selects the preferred external node by its numeric codes/node-id
     (not a display string); the direct-provider-bypass guard is registered in the flywheel.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.inference import oips
from src.teleon.inference import free_endpoint_intel as FE

_NOW = "2026-06-07T00:00:00Z"
_PREF = [{"preference_id": "p-redteam",
          "model_class_preference": {"tier_code": 600, "specialization_codes": [500]},
          "allowed_provider_nodes": ["model.anthropic.frontier@candidate", "model.local_stub@v1"],
          "disallowed_provider_nodes": [], "fallback_policy": {}, "data_policy": {}}]
_KEY_RE = re.compile(r"(sk-|gsk_|hf_|AIza|nvapi-)[A-Za-z0-9_\-]{16,}")


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    resolved = oips.resolve_preference(_PREF)
    route_nocreds = oips.select_provider(resolved, available_secrets=set())
    check("A: uncredentialed preferred external node → fallback recorded, not silent",
          route_nocreds["fallback_used"] is True and bool(route_nocreds["fallback_reason_codes"])
          and route_nocreds["selected_provider_node_id"] != "model.anthropic.frontier@candidate", json.dumps(route_nocreds))

    res = oips.infer_local(object_id="o1", preference_layers=_PREF, input_text="hello", now=_NOW)
    rcpt = res["receipt"]
    check("B: receipt allowed_use is never 'served' + llm_output_is_truth False",
          rcpt["allowed_use"] != "served" and rcpt["allowed_use"] in oips.ALLOWED_USE_ORDER
          and rcpt["policy_checks"]["llm_output_is_truth"] is False, json.dumps(rcpt["allowed_use"]))

    check("C: offline executes the LOCAL STUB (honest provenance, no network) even when a cloud node was preferred",
          rcpt["selected_provider_node_id"] == oips.OFFLINE_DEFAULT_NODE and res["output"].startswith("[local-stub"),
          rcpt["selected_provider_node_id"])

    fake_key = "sk-" + "R" * 30  # built dynamically; never a literal key
    res2 = oips.infer_local(object_id="o2", preference_layers=_PREF, input_text="my key is " + fake_key, now=_NOW)
    check("D: a raw key in the input never reaches the receipt (only input_hash)",
          fake_key not in json.dumps(res2["receipt"]) and res2["receipt"]["input_hash"].startswith("sha256:"))

    claw = FE.assess_gateway_repo({"repo_id": "open-gitagent/clawless", "role": "browser_agent_runtime",
                                   "signals": {"browser_runtime": True}})
    check("E: ClawLess → browser_agent_runtime (700), NOT an inference provider",
          claw["class_code"] == 700 and claw["is_inference_provider"] is False, json.dumps(claw))

    floor = FE._quarantine_floor()
    sk = FE.assess_gateway_repo({"repo_id": "rt.sharedkey", "role": "self_hosted_gateway",
                                 "signals": {"shared_key_markers": True}})
    check("F: shared-key/bypass repo → quarantine band", sk["class_code"] >= floor, str(sk["class_code"]))

    pol = json.loads((_REPO / "architecture" / "free_limited_llm_endpoint_policy.json").read_text())
    check("G: an official free/limited endpoint may NOT take customer-sensitive data (fail-closed)",
          pol["by_class"]["100"]["customer_sensitive_allowed"] is False)

    graph = oips.load_graph()
    external = [n for n in graph["nodes"] if n.get("external")]
    check("H: every external node uses a secret:// ref; no raw key anywhere in the graph",
          external and all(str(n.get("secret_ref", "")).startswith("secret://") for n in external)
          and not _KEY_RE.search(json.dumps(graph)),
          str([n["node_id"] for n in external if not str(n.get("secret_ref", "")).startswith("secret://")]))

    with_creds = oips.select_provider(resolved, available_secrets={"secret://provider/anthropic"})
    fly = (_REPO / "scripts" / "flywheel_proof_modules.py").read_text()
    check("I: credentialed → preferred external node selected by numeric codes/node-id; bypass guard registered",
          with_creds["selected_provider_node_id"] == "model.anthropic.frontier@candidate"
          and "check_no_direct_provider_bypass" in fly, with_creds["selected_provider_node_id"])

    print("\n" + ("PASS — check_inference_gateway_redteam: the shared LLM plane fails safely under attack — fallback "
                  "is recorded (never silent), the receipt is never 'served' and output is never truth, offline "
                  "runs the local stub with honest provenance and no raw key leak, ClawLess is a runtime not an "
                  "endpoint, shared-key repos quarantine, free endpoints refuse customer-sensitive data, external "
                  "nodes use secret refs, and routing is numeric." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_inference_gateway_redteam.py --self-test")
    raise SystemExit(0)
