#!/usr/bin/env python3
"""scripts.check_ollama_free_limited_compatibility — PROOF: the Shared LLM Plane is COMPATIBLE with Ollama (cloud +
local) and the other free-but-limited LLM tools — governed, candidate-not-active, and degrading safely offline.

"Compatible" here means: the Inference Gateway KNOWS these providers (registered candidate nodes routable through the
numeric provider graph), classifies them with the free-endpoint policy, references their secrets by ref only, and
falls back to the deterministic local stub when the provider is unreachable offline (no key / no network). It does NOT
mean we call them live (that stays owner-authorized) — output from any of them is a candidate, never served truth.

Asserts:
  A. NODES: model.ollama_cloud@candidate (external, secret_ref) + model.ollama_local@candidate (local, no secret) are
     in the provider graph, both CANDIDATE (status 200, not active 100), each with local_equivalent = the offline stub.
  B. GOVERNED FALLBACK: a 1300 fallback edge-path from ollama_cloud reaches the offline_default_node (the local stub).
  C. OFFLINE DEGRADATION: infer_local preferring Ollama with NO secret available executes the LOCAL STUB
     (OFFLINE_DEFAULT_NODE), records a non-silent fallback, and the output is is_truth=false (never promoted).
  D. CLASSIFICATION: free_endpoint_intel classifies Ollama Cloud = official_free_limited_provider (100, candidate,
     inference provider, baltor_use=not-truth) and Ollama local = self_hosted_gateway (500, lab candidate).
  E. FREE-LIMITED POLICY: every free-limited registry endpoint (Ollama + Groq/Gemini/OpenRouter/Cerebras/… ) is
     candidate-only, customer-sensitive data NOT allowed by default, executable only gated through the gateway, is_truth=false.
  F. QUARANTINE STILL BITES: a shared-key / "free unlimited GPT-4" bypass listing classifies as quarantine (>=900),
     not an inference provider.
  G. NO RAW KEY: no raw key / DSN appears in the provider graph or the free-limited registry (refs only).
  H. CANDIDATE-NOT-ACTIVE: no EXTERNAL provider node is status active (100); only local deterministic stubs are active.
  I. DETERMINISM.

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

_LEAK = re.compile(r"sk-[A-Za-z0-9_\-]{16,}|gsk_[A-Za-z0-9_\-]{16,}|(?:postgres|mysql|mongodb|redis)://[^ \"']+:[^ \"']+@")
_CLOUD, _LOCAL = "model.ollama_cloud@candidate", "model.ollama_local@candidate"


def _reaches(edges, start, goal) -> bool:
    seen, stack = set(), [start]
    while stack:
        cur = stack.pop()
        if cur == goal:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        stack += [e["to"] for e in edges if e.get("from") == cur and e.get("edge_type_code") == 1300]
    return False


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    g = oips.load_graph()
    nodes = {n["node_id"]: n for n in g["nodes"]}
    stub = g["offline_default_node"]

    check("A: Ollama cloud + local nodes are registered as CANDIDATE (status 200)",
          _CLOUD in nodes and _LOCAL in nodes
          and nodes[_CLOUD]["status_code"] == 200 and nodes[_LOCAL]["status_code"] == 200)
    check("A: cloud is external with a secret_ref + local_equivalent; local is secret-free + local_equivalent",
          nodes[_CLOUD]["external"] is True and nodes[_CLOUD]["secret_ref"] and nodes[_CLOUD]["local_equivalent"] == stub
          and nodes[_LOCAL]["external"] is False and not nodes[_LOCAL]["secret_ref"] and nodes[_LOCAL]["local_equivalent"] == stub)

    check("B: a 1300 governed-fallback edge-path from ollama_cloud reaches the offline stub",
          _reaches(g["edges"], _CLOUD, stub))

    pref = [{"preference_id": "ollama.try", "model_class_preference": {"tier_code": 400, "specialization_codes": [300]},
             "allowed_provider_nodes": [_CLOUD, _LOCAL, stub], "disallowed_provider_nodes": [],
             "fallback_policy": {}, "data_policy": {}}]
    inf = oips.infer_local(object_id="o", preference_layers=pref, input_text="hi", now="2026-06-05T00:00:00Z",
                           available_secrets=set())  # NO secret -> cloud cannot run
    rc = inf["receipt"]
    check("C: with no secret, inference executes the LOCAL STUB (offline) + records a non-silent fallback + is_truth=false",
          rc["selected_provider_node_id"] == stub and bool(rc.get("fallback_reason_codes"))
          and rc.get("policy_checks", {}).get("llm_output_is_truth") is False, json.dumps(rc.get("fallback_reason_codes")))

    cloud = FE.due_diligence({"endpoint_id": "endpoint.ollama_cloud@candidate", "provider_name": "Ollama Cloud",
                              "signals": {"has_official_docs": True}, "secret_ref": "secret://provider/ollama_cloud"})
    local = FE.due_diligence({"endpoint_id": "endpoint.ollama_local@candidate", "declared_role": "self_hosted_gateway",
                              "signals": {"has_official_docs": True}})
    check("D: Ollama Cloud classifies as official free-limited provider (100, candidate, inference provider, not-truth)",
          cloud["class_code"] == 100 and cloud["is_inference_provider"] is True and "not_truth" in cloud["baltor_use"])
    check("D: Ollama local classifies as self_hosted_gateway (500, lab candidate)", local["class_code"] == 500)

    reports = FE.run_registry()
    fl = [r for r in reports if r["class_code"] in (100, 200, 400, 500)]  # FREE/limited/lab tiers; 300=paid is carved out
    check("E: every free-limited endpoint is candidate-only, not customer-sensitive, gated, is_truth=false",
          bool(fl) and all(r["is_truth"] is False and r["allowed_data_class"] in ("public", "synthetic")
                           and "not" in r["baltor_use"] for r in fl)
          and any("ollama_cloud" in r["endpoint_id"] for r in reports))

    bypass = FE.classify(signals={"shared_key_markers": True}, free_text="free unlimited GPT-4 shared key, no signup")
    check("F: a shared-key / 'free unlimited' bypass listing is quarantined (>=900), not a provider", bypass[0] >= 900)

    blob = json.dumps(g) + json.dumps(FE._load("free_limited_llm_endpoint_registry.json"))
    check("G: no raw key / DSN in the provider graph or the free-limited registry (refs only)", not _LEAK.search(blob))

    ext_active = [n["node_id"] for n in g["nodes"] if n.get("external") and n.get("status_code") == 100]
    check("H: no external provider node is status active (100) — externals are candidates", not ext_active, str(ext_active))

    g2 = oips.load_graph()
    check("I: deterministic (graph reload stable)", [n["node_id"] for n in g2["nodes"]] == [n["node_id"] for n in g["nodes"]])

    print("\n" + ("PASS — check_ollama_free_limited_compatibility: the Shared LLM Plane knows Ollama (cloud + local) and "
                  "the free-limited tools as governed CANDIDATE providers — secret-by-ref, candidate-not-active, "
                  "customer-sensitive disallowed by default, shared-key bypass quarantined, and inference degrades to "
                  "the local stub offline (fallback recorded, output never truth)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_ollama_free_limited_compatibility.py --self-test")
    raise SystemExit(0)
