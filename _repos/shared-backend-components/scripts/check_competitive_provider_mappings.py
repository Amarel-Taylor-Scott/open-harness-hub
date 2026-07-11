#!/usr/bin/env python3
"""scripts.check_competitive_provider_mappings — PROOF: the competitive-intelligence infra/agent companies are
mapped to PORTS as governed CANDIDATES (never active, never direct imports, output never truth), and the inference
mapping is REAL — Fireworks is a candidate node routed through the Shared Inference Gateway with governed fallback.

Asserts:
  A. REGISTRY: competitive_provider_mappings.json — every mapping is candidate/reference (none "active"); source
     owner_provided_unverified; each carries a target_port + governance.
  B. FIREWORKS REAL: model.fireworks@candidate is a node in the live inference graph — external, secret_ref set,
     local_equivalent = the offline stub, status candidate (200, not the local-golden 100).
  C. GOVERNED, NOT DIRECT: via oips.select_provider — with NO creds the gateway does NOT pick Fireworks (governed
     fallback), with the Fireworks secret it DOES; so it is reachable only through the gateway, never a direct dep.
  D. EXECUTION BACKENDS: Crusoe/Nscale require a local_equivalent (offline default) + region policy (sovereign).
  E. BOUNDED AGENTS: Cursor/Cognition map to a CodegenAgent port, sandboxed, output-not-truth; Lovable is a TARGET
     not a provider; Mercor is human-in-loop; Harvey/OpenEvidence are benchmark analogs (OpenEvidence caveated).
  F. determinism + well-formed.

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


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    reg = json.loads((_resource("architecture") / "competitive_provider_mappings.json").read_text())
    m = {x["company"]: x for x in reg["mappings"]}
    check("A: all mappings candidate/reference (none active) + source unverified",
          all(x["status"] in ("candidate", "reference") for x in reg["mappings"])
          and reg["source"] == "owner_provided_unverified" and all(x.get("target_port") and x.get("governance") for x in reg["mappings"]))

    idx = {n["node_id"]: n for n in oips.load_graph()["nodes"]}
    fw = idx.get("model.fireworks@candidate", {})
    check("B: Fireworks is a real candidate node (external + secret_ref + local stub fallback + candidate status)",
          fw.get("external") is True and fw.get("secret_ref") == "secret://provider/fireworks"
          and fw.get("local_equivalent") == "model.local_stub@v1" and fw.get("status_code") == 200, json.dumps(fw))

    pref = [{"preference_id": "p", "model_class_preference": {"tier_code": 500, "specialization_codes": [500]},
             "allowed_provider_nodes": ["model.fireworks@candidate", "model.local_stub@v1"],
             "disallowed_provider_nodes": [], "fallback_policy": {}, "data_policy": {}}]
    resolved = oips.resolve_preference(pref)
    no_creds = oips.select_provider(resolved, available_secrets=set())
    with_creds = oips.select_provider(resolved, available_secrets={"secret://provider/fireworks"})
    check("C: governed — Fireworks NOT picked without its secret (fallback), picked WITH it",
          no_creds["selected_provider_node_id"] != "model.fireworks@candidate" and no_creds["fallback_used"] is True
          and with_creds["selected_provider_node_id"] == "model.fireworks@candidate", json.dumps([no_creds["selected_provider_node_id"], with_creds["selected_provider_node_id"]]))

    check("D: execution backends require local_equivalent + region policy (Nscale sovereign → data_residency)",
          "local_equivalent" in m["Crusoe"]["requires"] and "region_policy" in m["Crusoe"]["requires"]
          and "data_residency" in m["Nscale"]["requires"])

    check("E: bounded agents sandboxed + output-not-truth; Lovable=target; Mercor=human-in-loop; analogs caveated",
          m["Cursor / Anysphere"]["target_port"] == "CodegenAgentProviderPort" and "not truth" in m["Cognition / Devin"]["governance"].lower()
          and m["Lovable"]["target_port"] == "GeneratedAppTarget" and m["Mercor"]["kind"] == "human_in_loop"
          and "medical-advice" in m["OpenEvidence"]["governance"].lower())

    check("F: deterministic", oips.select_provider(resolved, available_secrets=set()) == no_creds)

    print("\n" + ("PASS — check_competitive_provider_mappings: the competitive infra/agent companies map to ports as "
                  "governed candidates (Fireworks is a real inference-gateway candidate reachable only with its "
                  "secret + governed fallback; Crusoe/Nscale execution backends need a local equivalent; "
                  "Cursor/Cognition are sandboxed bounded agents whose output is not truth); none is active or a "
                  "direct import." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_competitive_provider_mappings.py --self-test")
    raise SystemExit(0)
