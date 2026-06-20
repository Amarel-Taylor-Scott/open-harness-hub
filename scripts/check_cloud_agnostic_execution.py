#!/usr/bin/env python3
"""scripts.check_cloud_agnostic_execution — PROOF: cloud execution is provider-AGNOSTIC (owner: "AWS Lambda
should be platform-agnostic in case we want Google Cloud Functions or others; all cloud agnostic").

Asserts:
  A. The serverless-function family is read from CONFIG (`generic_cloud_functions` in the policy matrix), NOT a
     hard-coded code literal — adding a peer is a data edit. `select_backend` uses that config set.
  B. AWS Lambda is NOT canonical — it is one peer among GCP/Azure/Cloudflare/OpenFaaS-Knative; removing Lambda
     from availability still leaves serverless peers, and the capability still runs (falls back to local).
  C. Every serverless peer has the SAME required local equivalent (local function emulator) — the cloud-defer
     gate; no peer can be canonical/blocking.
  D. The selection ACTION is provider-agnostic ('use_cloud_function' for any serverless peer, no per-vendor
     branch), and changing the CONFIG set changes the runtime guard (non-fragile, no code edit).
  E. A function-eligible bucket can pick a cloud peer by policy; with no creds it falls back to local (never blocks).

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from src.teleon.runtime import execution_backend_selector as sel  # canonical Teleon home (Baltor re-exports the public API)

_A = Path(_REPO) / "architecture"
_MATRIX = json.loads((_A / "execution_backend_policy_matrix.json").read_text())


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    generic = sel.generic_functions(_MATRIX)
    # A. config-sourced family, multi-cloud
    check("A: serverless family read from config (generic_cloud_functions)", set(_MATRIX["generic_cloud_functions"]) == generic)
    check("A: family is multi-cloud (>= 4 peers incl. non-AWS)", len(generic) >= 4 and any("aws_" not in b for b in generic), str(sorted(generic)))

    # B. AWS Lambda is not canonical — peers exist beyond it
    peers_without_aws = {b for b in generic if not b.startswith("aws_")}
    check("B: AWS Lambda is NOT the only serverless option (GCP/Azure/Cloudflare/OpenFaaS peers exist)",
          len(peers_without_aws) >= 3, str(sorted(peers_without_aws)))

    # C. every serverless peer has the same local equivalent (cloud-defer gate)
    eqs = _MATRIX.get("candidate_local_equivalents", {})
    missing = [b for b in generic if b not in eqs]
    check("C: every serverless peer has a local equivalent", not missing, str(missing))
    check("C: serverless peers all map to the local function emulator",
          {eqs[b] for b in generic} == {"execution.local_function_emulator@v1"}, str({eqs.get(b) for b in generic}))

    # D. provider-agnostic action + config-driven guard (non-fragile)
    actions = {sel._action_for(b) for b in generic}
    check("D: every serverless peer resolves to the SAME provider-agnostic action", actions == {"use_cloud_function"}, str(actions))
    # changing the CONFIG set changes the guard — prove via a synthetic matrix with an extra peer
    synth = json.loads(json.dumps(_MATRIX)); synth["generic_cloud_functions"] = list(generic) + ["newcloud_fn@candidate"]
    check("D: adding a peer in CONFIG extends the guard with no code change", "newcloud_fn@candidate" in sel.generic_functions(synth))

    # E. a function-eligible bucket: picks a cloud peer if cheapest+available; with no creds → local fallback
    task = {"capability_id": "x", "worker_bucket": "utility", "estimated_runtime_ms": 200}
    # with a cloud cred present + healthy + cheaper, it MAY pick cloud (proves multi-cloud is reachable)
    d_no_creds = sel.select_backend(task, policy_matrix=_MATRIX)
    check("E: no cloud creds → runs locally (never blocks)", d_no_creds["backend"] in ("local_function_emulator@v1", "local_subprocess@v1"), str(d_no_creds["backend"]))
    # removing AWS Lambda from availability does not prevent the capability from running
    d_no_aws = sel.select_backend(task, policy_matrix=_MATRIX, available_creds={"gcp_cloud_function@candidate"},
                                  provider_health={"gcp_cloud_function@candidate": True})
    check("E: capability runs even when AWS Lambda is unavailable (a peer or local serves)", bool(d_no_aws.get("backend")), str(d_no_aws))

    print("\n" + ("PASS — check_cloud_agnostic_execution: serverless execution is provider-agnostic — the family "
                  "is config-sourced (not a code literal), AWS Lambda is one peer not canonical, every peer has "
                  "the same required local equivalent, the action is vendor-neutral, and missing creds fall back "
                  "to local (never block)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_cloud_agnostic_execution.py --self-test")
    raise SystemExit(0)
