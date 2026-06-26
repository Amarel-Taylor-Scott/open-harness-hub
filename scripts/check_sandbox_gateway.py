#!/usr/bin/env python3
"""scripts.check_sandbox_gateway — PROOF: the shared Sandbox Gateway runs candidates in a governed sandbox before
promotion — local golden path offline, external providers candidate-only, sandbox output is NOT truth.

Asserts:
  A. CONTRACTS + CATALOG: SandboxRunRequest/Result/Policy present + registered; provider catalog loads with a
     local offline_default.
  B. CATALOG GOVERNANCE: local providers active; every EXTERNAL provider is candidate WITH a local_equivalent;
     CubeSandbox is candidate, E2B-compatible, with risks + proof_to_promote (not golden path).
  C. LOCAL RUN (offline): a benign candidate command runs in the local sandbox → status ok, contract valid,
     receipt, deny-by-default (network none), is_truth False.
  D. SECRET HYGIENE: a planted secret env var is NOT passed into the sandbox; a candidate that emits a
     secret-looking token is flagged secrets_leaked + policy_violation.
  E. EXTERNAL = CANDIDATE, never the host: requesting sandbox.docker@candidate (no infra) → provider_unavailable,
     NOT silent host execution.
  F. SANDBOX OUTPUT IS NOT TRUTH: every result + receipt carries is_truth False (evidence for the gate only).
  G. NETWORK DENY-BY-DEFAULT: a request asking for network is recorded as a policy violation.
  H. DEPENDENCY LAW: no module under src/teleon/sandbox imports src.baltor.

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

from src.teleon import sandbox as SB
from src.teleon.sandbox import gateway as G

_NOW = "2026-06-06T00:00:00Z"


def _req(run_id, **kw):
    base = {"run_id": run_id, "capability_slot": "test", "candidate_artifact_id": "cand@v1", "command": [],
            "network_policy": "none", "filesystem_policy": "tempdir", "secret_policy": "none",
            "timeout_seconds": 15, "redteam_required": True}
    base.update(kw)
    return base


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    contracts = json.dumps(json.loads((_REPO / "architecture" / "contract_registry.json").read_text()))
    cat = SB.load_catalog()
    by_id = {p["provider_id"]: p for p in cat["providers"]}

    # A
    for c in ("SandboxRunRequest", "SandboxRunResult", "SandboxPolicy"):
        check(f"A: {c} registered", f"sandbox/{c}.schema.json" in contracts)
    check("A: catalog offline_default is local", cat["offline_default"] == SB.OFFLINE_DEFAULT_PROVIDER and by_id[cat["offline_default"]]["status"] == "active")

    # B
    ext = [p for p in cat["providers"] if p.get("external")]
    check("B: every external provider is candidate + has a local_equivalent",
          all(p["status"] == "candidate" and p.get("local_equivalent") for p in ext), str([p["provider_id"] for p in ext if not p.get("local_equivalent")]))
    cube = by_id.get("sandbox.cubesandbox@candidate", {})
    check("B: CubeSandbox candidate, E2B-compatible, risks + proof_to_promote",
          cube.get("status") == "candidate" and cube.get("e2b_compatible") and cube.get("risks") and cube.get("proof_to_promote"))

    # C local run
    r = SB.run_in_sandbox(_req("r1", command=["python3", "-c", "print('SANDBOX_OK')"], expected_outputs=["SANDBOX_OK"]), now=_NOW)
    check("C: local sandbox runs offline → ok + contract valid + receipt",
          r["status"] == "ok" and r["output_contract_valid"] and r["receipt_id"] and r["is_truth"] is False, json.dumps(r))

    # D secret hygiene (test tokens built dynamically so no literal sk- key appears in tracked source)
    _fake_key = "sk-" + "shouldnotleak123456"
    _fake_emit = "sk-" + "abcdefghijklmnop1234"
    os.environ["FAKE_OPENAI_API_KEY"] = _fake_key
    try:
        r2 = SB.run_in_sandbox(_req("r2", command=["python3", "-c", "import os;print('HASKEY' if os.environ.get('FAKE_OPENAI_API_KEY') else 'NOKEY')"], expected_outputs=["NOKEY"]), now=_NOW)
        check("D: secret env NOT passed into sandbox", r2["output_contract_valid"] and "NOKEY" in r2["stdout_sample"], r2["stdout_sample"])
        r3 = SB.run_in_sandbox(_req("r3", command=["python3", "-c", f"print('{_fake_emit}')"]), now=_NOW)
        check("D: emitted secret-looking token flagged (secrets_leaked + violation)",
              r3["secrets_leaked"] and "secret_in_output" in r3["policy_violations"], json.dumps(r3))
    finally:
        os.environ.pop("FAKE_OPENAI_API_KEY", None)

    # E external candidate never runs on host
    r4 = SB.run_in_sandbox(_req("r4", command=["echo", "x"]), provider_id="sandbox.docker@candidate", now=_NOW)
    check("E: external candidate → provider_unavailable (no host execution)", r4["status"] == "provider_unavailable" and r4["exit_code"] is None, json.dumps(r4))

    # F not truth
    check("F: results + receipts are NOT truth", all(x["is_truth"] is False for x in (r, r2, r3, r4)))

    # G network deny-by-default
    r5 = SB.run_in_sandbox(_req("r5", command=["python3", "-c", "print(1)"], network_policy="full"), now=_NOW)
    check("G: requesting network → policy violation", "network_requested_but_denied_by_default" in r5["policy_violations"], json.dumps(r5["policy_violations"]))

    # H dependency law
    bad = [str(p.relative_to(_REPO)) for p in (_REPO / "src" / "teleon" / "sandbox").rglob("*.py")
           for line in p.read_text().splitlines() if line.strip().startswith(("import src.baltor", "from src.baltor"))]
    check("H: no src/teleon/sandbox module imports src.baltor", not bad, "; ".join(bad))

    print("\n" + ("PASS — check_sandbox_gateway: candidates run in a governed local sandbox (deny-by-default: no "
                  "network, no secrets, scoped tempdir, timeout); external providers (Docker/E2B/Daytona/"
                  "CubeSandbox/K8s) are candidate-only behind the port with local equivalents and never run on the "
                  "host; sandbox output is never truth — it is evidence for the promotion gate."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_sandbox_gateway.py --self-test")
    raise SystemExit(0)
