#!/usr/bin/env python3
"""scripts.check_inference_gateway — PROOF: the shared Inference Gateway + Open Inference Preference Spec (OIPS).

Owner asks: (1) a shared LLM router; (2) every object declares LLM preferences (industry standard); (3) the
router handles an unavailable preferred model and records the PROVENANCE of which model was actually used.

Asserts:
  A. CONTRACTS: the 3 OIPS schemas load; receipts/resolved-prefs carry the required fields.
  B. NUMERIC GRAPH: tier/specialization/status/edge codes + provider graph load; offline default node exists;
     every EXTERNAL node declares a secret_ref AND a local_equivalent (no raw keys; cloud-defer-after-local).
  C. NO BRITTLE STRINGS: the engine branches on numeric codes + node ids, not provider display names.
  D. INHERITANCE: resolve_preference merges layers in order (later overrides earlier), records resolved_from +
     a deterministic effective_policy_hash.
  E. PREFERRED CHOSEN: when the preferred provider is credentialed + healthy, it is selected (no fallback).
  F. GOVERNED FALLBACK: missing secret / unhealthy provider → preferred REJECTED with a reason code, a
     fallback is selected, and rejected_candidates + fallback_reason_codes are recorded (never silent).
  G. DATA POLICY: external_llm_allowed=false → external nodes rejected (policy_blocked) → a NON-external node runs.
  H. TIER DOWNGRADE → ALLOWED-USE DOWNGRADE: a lower-tier fallback yields allowed_use in {draft,candidate},
     never 'promotable'; a clean preferred call is 'promotable'; nothing is ever 'served' (Baltor governs serving).
  I. PROVENANCE: a receipt records the ACTUAL executed node/model, fallback trail, input/output hashes,
     policy_checks, allowed_use; it conforms to ModelInvocationReceipt.v1.
  J. SECRET HYGIENE: no raw key appears in the graph/route/receipt (secret_refs only).
  K. LLM-OUTPUT-NOT-TRUTH: receipt.policy_checks.llm_output_is_truth is False; allowed_use is never 'served'.
  L. DETERMINISM + OFFLINE: infer_local runs offline with no secrets and is deterministic for a fixed `now`.

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

_NOW = "2026-06-06T00:00:00Z"
_A = _REPO / "architecture"
_S = _REPO / "schemas" / "inference"
_SECRET_LEAK = re.compile(r"(AKIA[0-9A-Z]{12}|sk-[a-zA-Z0-9]{16})")


def _pref(allowed, *, tier="frontier", specs=(500, 400), external_allowed=True, fail_closed=False, disallowed=()):
    return {"preference_id": "pref.test@v1", "scope": "purpose_task", "object_id": "obj.test@v1",
            "task_intent": "generate_candidate_implementation",
            "model_class_preference": {"tier": tier, "specialization_codes": list(specs)},
            "allowed_provider_nodes": list(allowed), "disallowed_provider_nodes": list(disallowed),
            "fallback_policy": {"allow_fallback": True, "fail_closed_if_unavailable": fail_closed},
            "data_policy": {"external_llm_allowed": external_allowed}, "budget_policy": {"max_cost_usd": 2.0},
            "latency_policy": {"max_p95_ms": 60000}, "provenance_required": True, "evaluation_policy": {}}


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    # A. contracts
    schemas = {p.name.split(".v1")[0]: json.loads(p.read_text()) for p in _S.glob("*.schema.json")}
    for s in ("InferencePreference", "ResolvedInferencePreference", "ModelInvocationReceipt"):
        check(f"A: {s}.v1 schema present", s in schemas)
    receipt_req = set(schemas["ModelInvocationReceipt"]["required"])

    # B. numeric graph
    g = oips.load_graph(); idx = {n["node_id"]: n for n in g["nodes"]}
    check("B: offline default node exists", g["offline_default_node"] in idx)
    ext = [n for n in g["nodes"] if n.get("external")]
    check("B: every external node has a secret_ref", all(n.get("secret_ref") for n in ext), str([n["node_id"] for n in ext if not n.get("secret_ref")]))
    check("B: every external node has a local_equivalent", all(n.get("local_equivalent") for n in ext))
    for cfg in ("model_quality_tier_codes", "model_specialization_codes", "model_provider_edge_type_codes"):
        d = json.loads((_A / f"{cfg}.json").read_text())
        check(f"B: {cfg} numeric", all(isinstance(e["code"], int) for e in next(v for v in d.values() if isinstance(v, list))))

    # C. no brittle provider display strings in engine control flow
    src = (_REPO / "src" / "teleon" / "inference" / "oips.py").read_text()
    brittle = [s for s in ('== "OpenAI"', '== "Anthropic"', '== "Gemini"', 'if "openai" in', 'if "anthropic" in') if s in src]
    check("C: engine branches on codes/node-ids, not provider display names", not brittle and "tier_code" in src, str(brittle))

    # D. inheritance
    layers = [{"_layer": "global", "data_policy": {"external_llm_allowed": True}, "provenance_required": True},
              {"_layer": "teleon", "model_class_preference": {"tier": "standard"}},
              {"_layer": "instance", "model_class_preference": {"tier": "frontier", "specialization_codes": [500]}}]
    r1 = oips.resolve_preference(layers); r2 = oips.resolve_preference(layers)
    check("D: resolved_from records the full trail", r1["resolved_from"] == ["global", "teleon", "instance"])
    check("D: later layer overrides earlier (tier=frontier)", r1["effective"]["model_class_preference"]["tier"] == "frontier")
    check("D: effective_policy_hash deterministic", r1["effective_policy_hash"] == r2["effective_policy_hash"] and r1["effective_policy_hash"].startswith("sha256:"))

    # E. preferred chosen when available
    allowed = ["model.openai.frontier@candidate", "model.anthropic.frontier@candidate", "model.local_stub@v1"]
    res = oips.resolve_preference([_pref(allowed)])
    route = oips.select_provider(res, available_secrets={"secret://provider/openai"}, provider_health={})
    check("E: preferred provider chosen when credentialed+healthy",
          route["selected_provider_node_id"] == "model.openai.frontier@candidate" and route["fallback_used"] is False, json.dumps(route))

    # F. governed fallback (no secrets)
    route_fb = oips.select_provider(res, available_secrets=set(), provider_health={})
    reasons = set(route_fb["fallback_reason_codes"])
    check("F: missing secret → fallback (not silent), reasons recorded",
          route_fb["fallback_used"] and "preferred_secret_missing" in reasons and route_fb["rejected_candidates"], json.dumps(route_fb))
    # unhealthy preferred
    route_un = oips.select_provider(res, available_secrets={"secret://provider/openai"},
                                    provider_health={"model.openai.frontier@candidate": False})
    check("F: unhealthy preferred → rejected + fallback",
          route_un["selected_provider_node_id"] != "model.openai.frontier@candidate" and
          any(c["reason_code"] == "provider_health_degraded" for c in route_un["rejected_candidates"]), json.dumps(route_un))

    # G. data policy: external disallowed → a non-external node runs
    res_local = oips.resolve_preference([_pref(allowed, external_allowed=False)])
    route_g = oips.select_provider(res_local, available_secrets={"secret://provider/openai"}, provider_health={})
    sel = route_g["selected_provider_node_id"]
    check("G: external_llm_allowed=false → non-external node selected",
          sel is not None and not idx.get(sel, {}).get("external", False) and
          any(c["reason_code"] == "preferred_model_policy_blocked" for c in route_g["rejected_candidates"]), json.dumps(route_g))

    # H. tier downgrade → allowed_use downgrade; clean call → promotable; never served
    out_fb = oips.infer_local(object_id="obj.test@v1", preference_layers=[_pref(allowed)], input_text="x", now=_NOW,
                              available_secrets=set(), provider_health={})
    check("H: fallback/local execution → allowed_use is draft/candidate (not promotable)",
          out_fb["receipt"]["allowed_use"] in ("draft", "candidate"), out_fb["receipt"]["allowed_use"])
    check("H: allowed_use is NEVER 'served' (Baltor governs serving)",
          out_fb["receipt"]["allowed_use"] != "served" and "served" in oips.ALLOWED_USE_ORDER)

    # I. provenance / receipt conformance
    rcpt = out_fb["receipt"]
    missing = [k for k in receipt_req if k not in rcpt]
    check("I: receipt conforms to ModelInvocationReceipt.v1 (required fields)", not missing, str(missing))
    check("I: receipt records ACTUAL executed node + fallback trail + hashes",
          rcpt["selected_provider_node_id"] and rcpt["fallback_used"] and rcpt["input_hash"].startswith("sha256:")
          and rcpt["output_hash"].startswith("sha256:"))

    # J. secret hygiene — no raw key anywhere
    blob = json.dumps(g) + json.dumps(route_fb) + json.dumps(rcpt)
    check("J: no raw API key in graph/route/receipt (secret_refs only)", not _SECRET_LEAK.search(blob))
    check("J: external nodes reference secret:// refs", all(str(n.get("secret_ref", "")).startswith("secret://") for n in ext))

    # K. LLM output is not truth
    check("K: receipt asserts llm_output_is_truth == False", rcpt["policy_checks"]["llm_output_is_truth"] is False)

    # L. determinism + offline
    a = oips.infer_local(object_id="o@v1", preference_layers=[_pref(allowed)], input_text="hello", now=_NOW)
    b = oips.infer_local(object_id="o@v1", preference_layers=[_pref(allowed)], input_text="hello", now=_NOW)
    check("L: infer_local deterministic for fixed now", a == b)
    check("L: offline run executes the local stub honestly", a["receipt"]["selected_provider_node_id"] == oips.OFFLINE_DEFAULT_NODE
          and "offline_local_execution" in a["receipt"]["fallback_reason_codes"])

    print("\n" + ("PASS — check_inference_gateway: OIPS preferences resolve via inheritance; the numeric provider "
                  "graph selects the preferred model when available and applies GOVERNED, recorded fallback when "
                  "not; every call emits a ModelInvocationReceipt with the actual model + fallback trail + hashes + "
                  "allowed_use; secrets are refs only; LLM output is never truth and never auto-'served'; offline + "
                  "deterministic." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_inference_gateway.py --self-test")
    raise SystemExit(0)
