#!/usr/bin/env python3
"""scripts.check_shared_io_resource_full_stack — PROOF: the Shared I/O + Resource Spine composes END-TO-END.

One deterministic scenario threads a single tenant request through EVERY spine layer and asserts the cross-cutting
invariants hold across the whole chain — the layers fit together, not just in isolation. Complements the per-layer
proofs (spine, command/work, event, inference) + the standalone redteam.

Scenario (one correlation_id throughout):
  RESOURCE  -> declare + validate a persistent table (owner+retention) and a temp dataset (ttl); a provision receipt.
  WORK      -> a leased task is claimed (WorkerClaim) and acked succeeded (AckNackReceipt, explicit worker).
  EVENT     -> a bus event with a secret in its payload is projected to a CloudEvents envelope — secret REDACTED.
  INFERENCE -> an InferenceRequest stores the input HASH (not the raw prompt); select_provider -> ModelRouteDecision;
               infer_local executes the LOCAL STUB offline with a ModelInvocationReceipt (is_truth=false).
  OBJECTSHELL-> the resulting ContextArtifact is wrapped in ObjectShell LOSSLESSLY (rehydrate == original).

Asserts:
  A. RESOURCE layer: both specs validate; provision receipt is well-formed (cleanup_required reflects ownership).
  B. WORK layer: a WorkerClaim needs a lease; the ack receipt is succeeded + records the explicit worker.
  C. EVENT layer: the envelope carries the correlation_id and the secret is REDACTED out of the data.
  D. INFERENCE layer: the request carries an input_hash (never the raw prompt); the route decision is a
     ModelRouteDecision; the receipt is is_truth=false and executed the offline stub.
  E. OBJECTSHELL layer: the artifact wraps losslessly (rehydrate == original).
  F. TRACING: one correlation_id threads the event chain.
  G. NO RAW SECRET across ALL produced artifacts (one final scan over the whole chain).
  H. DETERMINISM: re-running the scenario yields byte-identical artifacts.

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

from src.teleon.resources import resource_ref as R
from src.teleon.io import event_io as E, work_io as W, inference_io as I, object_shell_migration as OSM
from src.teleon.inference import oips
from scripts.context_events import EVENT_KINDS

_NOW = "2026-06-05T00:00:00Z"
_CID = "corr-fullstack-001"
_SECRET = "sk-" + "a1b2c3d4" * 6
_LEAK = re.compile(r"sk-[A-Za-z0-9_\-]{16,}|gsk_[A-Za-z0-9_\-]{16,}|(?:postgres|mysql|mongodb|redis)://[^ \"']+:[^ \"']+@")


def _scenario() -> dict:
    """Run the whole chain once; return every produced artifact (deterministic)."""
    # RESOURCE
    persist = R.make_data_resource_spec(logical_name="facts_main", kind_code=R.KIND["relational_table"],
                                        ownership_code=R.MANAGED_PERSISTENT, owner="team", retention_class="standard")
    temp = R.make_data_resource_spec(logical_name="scratch", kind_code=R.KIND["relational_table"],
                                     ownership_code=R.MANAGED_EPHEMERAL, ttl_seconds=3600)
    receipt = R.provision_receipt(persist, now=_NOW)
    # WORK
    task = {"task_id": "t-1", "status": "running", "lease_owner": "w-1", "lease_until": _NOW,
            "claimed_at": _NOW, "attempt": 1, "result_artifact_ids": []}
    claim = W.project_worker_claim(task)
    ack = W.project_ack_nack_receipt({**task, "status": "succeeded"}, outcome="ack", worker_id="w-1", retryable=None)
    # EVENT (secret in payload -> must be redacted)
    kind = "receipt_issued" if "receipt_issued" in EVENT_KINDS else sorted(EVENT_KINDS)[0]
    env = E.project_event_envelope({"seq": 1, "kind": kind, "correlation_id": _CID,
                                    "payload": {"api_key": _SECRET, "answer": "10 business days"}},
                                   source="fullstack", now=_NOW, valid_kinds=EVENT_KINDS)
    # INFERENCE (secret in the prompt -> only the hash is stored)
    req = I.make_inference_request(object_id="o-1", requested_model_class="tier:400/300",
                                   input_text="draft using " + _SECRET, now=_NOW, preference_id="p")
    pref = [{"preference_id": "p", "model_class_preference": {"tier_code": 400, "specialization_codes": [300]},
             "allowed_provider_nodes": ["model.local_stub@v1"], "disallowed_provider_nodes": [],
             "fallback_policy": {}, "data_policy": {}}]
    route = oips.select_provider(oips.resolve_preference(pref), available_secrets=set())
    route_decision = I.project_route_decision(route)
    inf = oips.infer_local(object_id="o-1", preference_layers=pref, input_text="draft using " + _SECRET, now=_NOW)
    # OBJECTSHELL (wrap the resulting context artifact losslessly)
    ca = {"kind": "context_artifact", "context_artifact_id": "ctxart_fs_1", "artifact_type": "context_pack",
          "derived_from": ["ctx://acme/source/BILL-782"], "content_hash": "sha256:" + "f" * 64,
          "created_at": _NOW, "policy": {"visibility": "internal"}}
    shell = OSM.migrate_to_shell(ca, object_type="ContextArtifact", id_field="context_artifact_id",
                                 source_schema="schemas/context-artifact.schema.json", now=_NOW)
    return {"persist": persist, "temp": temp, "receipt": receipt, "claim": claim, "ack": ack, "env": env,
            "req": req, "route_decision": route_decision, "inf_receipt": inf["receipt"], "shell": shell, "ca": ca}


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    s = _scenario()

    okP, _ = R.validate_resource_spec(s["persist"])
    okT, _ = R.validate_resource_spec(s["temp"])
    check("A: resource layer — persistent + temp specs validate; provision receipt well-formed",
          okP and okT and s["receipt"]["schema_version"] == "ResourceProvisionReceipt" and s["receipt"]["cleanup_required"] is False)

    check("B: work layer — WorkerClaim holds the lease + ack is succeeded with the explicit worker",
          s["claim"]["schema_version"] == "WorkerClaim" and s["claim"]["worker_id"] == "w-1"
          and s["ack"]["resulting_status"] == "succeeded" and s["ack"]["worker_id"] == "w-1")

    check("C: event layer — envelope carries the correlation_id + the secret is REDACTED",
          s["env"]["correlation_id"] == _CID and _SECRET not in json.dumps(s["env"]) and "[REDACTED]" in json.dumps(s["env"]["data"]))

    check("D: inference layer — request stores the input HASH not the raw prompt",
          s["req"].get("input_hash", "").startswith("sha256:") and _SECRET not in json.dumps(s["req"]))
    check("D: inference layer — route decision is a ModelRouteDecision + receipt is_truth=false, executed offline stub",
          "RouteDecision" in s["route_decision"].get("schema_version", "")
          and s["inf_receipt"]["selected_provider_node_id"] == oips.OFFLINE_DEFAULT_NODE
          and s["inf_receipt"]["policy_checks"]["llm_output_is_truth"] is False)

    check("E: objectshell layer — the artifact wraps losslessly (rehydrate == original)", OSM.rehydrate(s["shell"]) == s["ca"])

    check("F: tracing — one correlation_id threads the chain", s["env"]["run_id"] == _CID and s["env"]["correlation_id"] == _CID)

    blob = json.dumps({k: v for k, v in s.items()})
    check("G: NO raw secret/DSN across ALL produced artifacts", not _LEAK.search(blob), "leak in chain")

    s2 = _scenario()
    check("H: deterministic — re-running the scenario is byte-identical",
          json.dumps(s, sort_keys=True) == json.dumps(s2, sort_keys=True))

    print("\n" + ("PASS — check_shared_io_resource_full_stack: the Shared I/O + Resource Spine composes end-to-end — "
                  "resource specs validate, work is lease-gated, events redact secrets + carry the correlation_id, "
                  "inference stores the input hash + never serves truth, the artifact wraps into ObjectShell "
                  "losslessly, and no raw secret crosses any layer." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_shared_io_resource_full_stack.py --self-test")
    raise SystemExit(0)
